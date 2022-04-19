import os
import pandas as pd
import numpy as np
from .base import Standard_Template
import sys
import warnings
if not sys.warnoptions:
    warnings.simplefilter("ignore")


class MIMIC_Data(Standard_Template):
    """The data template to store MIMIC data. Customized fields can be added
    in each parse_xxx methods.

    Parameters
        ----------
        patient_id

        time_duration

        selection_method
    """

    def __init__(self, patient_id, time_duration, selection_method):
        super(MIMIC_Data, self).__init__(patient_id=patient_id)
        self.time_duration = time_duration
        self.selection_method = selection_method

    def parse_patient(self, pd_series, mapping_dict=None):
        if mapping_dict is None:
            self.data['gender'] = pd_series['pa_gender'].values[0]
            self.data['dob'] = pd_series['year_born'].values[0]
        else:
            self.data['gender'] = pd_series[mapping_dict['pa_gender']].values[0]
            self.data['dob'] = int(pd_series[mapping_dict['year_born']].values[0])
            print(self.data)

    def parse_admission(self, pd_df):
        # TODO: implement the mapping dict
        for ind, row in pd_df.iterrows():
            # each admission is stored as a seperate dictionary and
            # added to admission_list
            admission_event = {}
            admission_event['admission_id'] = int(row['epi_id'])
            admission_event['admission_date'] = row['epi_StartOfEpisode']
            admission_event['discharge_date'] = row['epi_EndOfEpisode']
            admission_event['death_indicator'] = int(
                #~pd.isna(pd_df['mortality']).values[0])
                  pd_df['mortality'].values[0])
            # more elements can be added here
            self.data['admission_list'].append(admission_event)

    def parse_icu(self, pd_df, mapping_dict=None):
        if len(self.data['admission_list']) == 0:
            raise ValueError(
                "No admission information found. Parse admission info first.")

        for i, admission_event in enumerate(self.data['admission_list']):
            # print(ind, self.data['patient_id'], admission_event['admission_id'])
            temp_df = pd_df.loc[
                pd_df['epi_id'] == admission_event['admission_id']]
            # print(temp_df.shape)
            for ind, row in temp_df.iterrows():
                admission_event['icustay_id'] = int(row['ceo_id'])

            self.data['admission_list'][i] = admission_event

    def parse_event(self, pd_df, save_dir='', event_mapping_df='',
                    var_list=None):

        if len(self.data['admission_list']) == 0:
            raise ValueError(
                "No admission information found. Parse admission info first.")

        # make saving directory if needed
        if not os.path.isdir(save_dir):
            os.mkdir(save_dir)

        for i, admission_event in enumerate(self.data['admission_list']):

            # get all the events
            temp_df = pd_df.loc[
                pd_df['epi_id'] == admission_event['admission_id']]

            if not temp_df.empty:
                # save csv location
                # raw event
                admission_event['event_csv'] = str(
                    self.data['patient_id']) + '_' + str(
                    admission_event['admission_id']) + '.csv' 

                # sort it by the date and time
                temp_df = temp_df.sort_values(by='M0090_INFO_COMPLETED_DT')

                first_index = temp_df['M0090_INFO_COMPLETED_DT'].index[0]
                # print(temp_df['charttime'][first_index])
                temp_df['first_entry'] = pd.to_datetime(
                    temp_df['M0090_INFO_COMPLETED_DT'][first_index])

                # calculate the time difference in seconds since the first entry
                temp_df['secs_since_entry'] = ((pd.to_datetime(temp_df['M0090_INFO_COMPLETED_DT']) - temp_df[
                    'first_entry']).dt.total_seconds() // 86400)
                # speed up by dropping date format
                temp_df['charttime'] = temp_df['M0090_INFO_COMPLETED_DT'].astype(str)
                temp_df['first_entry'] = temp_df['first_entry'].astype(str)

                # save the raw event data to local csv
                temp_df.to_csv(
                    os.path.join(save_dir, admission_event['event_csv']),
                    index=False)
                # generate episode data
                # handle all events data by aggregation during a time window
                episode_df = self.generate_episode(
                    temp_df, duration=self.time_duration,
                    event_mapping_df=event_mapping_df,
                    var_list=var_list)

                if episode_df.shape[0] >= 2:
                    # save episode location only if there are more than 2 sequencnes
                    # do not save if it is empty or just a single sequence
                    admission_event['episode_csv'] = str(
                        self.data['patient_id']) + '_' + str(
                        admission_event['admission_id']) + '_episode.csv'

                    # save the episode data to local csv
                    episode_df.to_csv(
                        os.path.join(save_dir, admission_event['episode_csv']),
                        index=False)

                # update the dictionary
                self.data['admission_list'][i] = admission_event

        return temp_df  # for debug purpose

    def write_record(self, temp_list, temp_df, var):
        # TODO: this may be sped up by aggreagte on itemid, and then use the last one
        if not temp_df.empty:
            if self.selection_method == 'last':
                # take the last record within the range
                temp_list.append(temp_df.iloc[-1]['value']) #This gets the last row and the value cell
            elif self.selection_method == 'mean':
                temp_list.append(temp_df['value'].mean())
                # if there is no information, just skip
        else:
            temp_list.append('')

        return temp_list

    def generate_episode_headers(self, var_list):
        """Generate the header for episode file

        Parameters
        ----------
        var_list

        Returns
        -------

        """

        self.episode_headers_ = ['secs_since_entry'] # This is the first item in the list.
        for var in var_list:
            # self.episode_headers_.extend([var, var + '_unit'])
            self.episode_headers_.append(var)

    def generate_episode(self, pd_df, duration, event_mapping_df, var_list):


        self.generate_episode_headers(var_list)
        #pd_df.rename(columns={'M0090_INFO_COMPLETED_DT': 'secs_since_entry'}, inplace=True)

        # when it is in the memory, process it directly
        max_time_diff = pd_df['secs_since_entry'].max() # number of days from first visit in episode
        #max_time_diff = pd_df['M0090_INFO_COMPLETED_DT'].max() 
        #max_time_diff = 1000000

        # only keep the events we are interested in
        key_df = event_mapping_df[event_mapping_df['OASIS'].isin(var_list)]

        # rounding up
        #n_episode = int(np.ceil(max_time_diff / duration))
        n_episode = int(pd_df['secs_since_entry'].nunique())

        # print(n_episode)   

        episode_df = pd.DataFrame(columns=self.episode_headers_)

        for j in range(n_episode):
            threshold_l = j * duration
            threshold_h = (j + 1) * duration

            # find all the events within the duration
            # by placing a boolean inside .loc we end up filtering the entire df (keeping rows) based 
            # on whether the columns are T/F
            #slice_df = pd_df.loc[(pd_df['secs_since_entry'] >= threshold_l) & (
            #        pd_df['secs_since_entry'] < threshold_h)]
            slice_df = pd_df.loc[pd_df.secs_since_entry == pd_df.secs_since_entry.unique()[j]].fillna(0)
            

            # need some sort on the time so just get the last value within the range
            # can join on multiple things, weight for instance
            # the starting point is the key_df with only the var_headers we want
            # This is where we pull in the data
            temp_df = key_df.merge(slice_df, left_on='itemID',
                                   right_on='itemID', suffixes=(None, '_delete')).drop(axis=1, columns=['OASIS_delete'], level=None, inplace=False, errors='raise')


            # valid information is available, otherwise skip            
            if not temp_df.empty:
                temp_df.sort_values(by='secs_since_entry', inplace=True)

                # initialize the record with timestamp
                temp_list = [threshold_h]

                # iterate over variables at interests
                for var in var_list:
                    print(var)
                    var_df = temp_df[temp_df['OASIS'] == var] # This is wrong
                    #var_df = temp_df[temp_df['variable'] == var]
                    # write records for each variable at interest
                    temp_list = self.write_record(temp_list, var_df, var)

                # append to the major episode dataframe
                epi_df = pd.DataFrame(temp_list).transpose()
                epi_df.columns = self.episode_headers_
                episode_df = pd.concat([episode_df, epi_df], axis=0)

                # ###############################################################
                # # need to iterate over rows, may not be sufficiently faster.
                # # on park
                # get the last record for each variable
                # episode_df = temp_df.groupby(['level2']).agg({
                #     'itemid' : 'last',
                #     'value' : 'last',
                #     'valueuom' : 'last',
                #     })                
                # self.a = episode_df
                # print(episode_df)
                # ###############################################################

        # return the episode df 
        return episode_df


##############################################################################

def parallel_parse_tables(patient_id_list, patient_df, admission_df, icu_df,
                          event_df, event_mapping_df, duration,
                          selection_method, var_list, save_dir):
    """Parallel methods to process patient information in batches

    Parameters
    ----------
    patient_id_list
    patient_df
    admission_df
    icu_df
    event_df
    var_list

    Returns
    -------

    """
    valid_data_list, valid_id_list = [], []

    # for i in tqdm(range(len(patient_id_list))):
    for i in range(len(patient_id_list)):
        p_id = patient_id_list[i]
        # print('Processing Patient', i + 1, p_id)
        # initialize the 
        temp_data = MIMIC_Data(p_id, duration, selection_method)
        p_df = patient_df.loc[patient_df['pa_id'] == p_id]
        a_df = admission_df.loc[admission_df['pa_id'] == p_id]
        i_df = icu_df.loc[icu_df['pa_id'] == p_id]
        e_df = event_df.loc[event_df['pa_id'] == p_id]

        if not p_df.empty:
            if p_df.shape[0] > 1:
                raise ValueError("Patient ID cannot be repeated")
            temp_data.parse_patient(p_df)

        if not a_df.empty:
            temp_data.parse_admission(a_df)
        if not i_df.empty:
            temp_data.parse_icu(i_df)

        if not e_df.empty:
            temp_data.parse_event(e_df, save_dir=save_dir,
                                  event_mapping_df=event_mapping_df,
                                  var_list=var_list)

        valid_data_list.append(temp_data)
        valid_id_list.append(p_id)

    return valid_data_list, valid_id_list
