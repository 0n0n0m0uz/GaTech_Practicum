# GaTech_Practicum

*This was built in the linux subsystem for Windows, so all instructions are assuming a linux environment*

## Instructions to Replicate this model on your machine.

1. Clone this github repo to your local machine via two possible methods:
   - Hit the Green 'Code' button above and download zip
   - using command line and `git clone`

2. Move the cloned folder into your Jupyter server base folder, or direct Jupyter web client to correct folder location.

3. You should create a local conda environment via the below command and using the environment.yml file which has all the packages needed: 

      `conda env create -f /path/to/environment.yml`

4. Activate the conda environment you created:
       `activate pyhospice'

5. Launch Jupyter Notebook
 
6. The Jupyter Notebooks are executed in order to replicate the results on your own local machine. Follow the documentation in the notebooks for detailed explanations of each step

01_Clean_RawData.........
> **Import CSV data** You may have to convert excel file to csv. This step takes final version of Compassus data file as input <br>
> **Data Exploration** - Runs SweetViz report, functionality to eliminate columns of your choosing, functions to clean up duplicates, fix errors in data <br>
> **Class Labels** - label the patients mortality class (1 or 0) depending on whether they died within 365 days or lived longer than 365 days. <br>
> **Export Cleaned up CSV** - From this point forward forget about the original dataset and use this cleaned up version for further processing. <br>

02_Create_Patient_Episode.........
> The 2nd Jupyter File will take the cleaned up csv from step 1 and re-organize it into a standardized format more effective for model input.  It will create separate dataframes and csv files for patients, episodes, visits, and events and export them.

03_Create_Models_for_Mortality_Predict....
> The 3rd notebook will import the CSV from step 2 and then setup and execute the model.  There are steps to extract feature info into a better format and then run the LTSM model.  Basically, it will create a separate episode file for each patient.  These files need to be moved into the x_data folder.  In a separate step the labels are created into a separate csv file with need to be in the y_data folder.

I am going to work on automating even futher before the presentation.


### You can see my report in the Final_Practicum_Levesque.pdf file

The objective of this analysis was to take the patient-level electronic healthcare data and develop a model that could predict mortality within 1 year.  Patients who the model determines have the highest likelihood of perishing will be moved from regular home health care and into hospice care.  Accurate predictions offer benefits to both patients and providers as resources can be allocated more effectivley and the proper attention and care can be prioritized to those patients with the most urgent needs.  There are economic benefits as well as quality of life benefits which is a strong incentive for research into new and improved prediction approaches.  


---
All this text below was just me thinking outloud before I wrote the paper.  It's not really important.

### Model Chosen


---

For the model, I decided to try and implement an LSTM deep learning model because I had never done it before and figured I should try something I don't know how to do.  My results were not the best with about 65% accuracy.  No doubt the data integrity issues may be affecting things.



Garbage in - Garbage out has never been more true than with healthcare data I have learned.


# Background on The Home Health Care Industry and Hosice

## Government Agencies

## Need for Standardization 

There is a push by the federal government to improve health care reporting standards and the OASIS standards are just one example. The Office National Coordinator for Health Care Policy (ONC) entire mission is working to standardize Electronic Health Records (EHR) to allow for interagency coordination which would make anyone who deals with health care data lives easier.  It is hard to overstate just how important this is in terms of research and improving the ability of technological tools to improve healthcare outcomes going forward.  So much time and effort is currently spent just on cleaning data that really has an impact on the quality of the models and thus the trust and confidence on the results 

## Background on this particular task

# Data

The dataset itself as is common in the health care industry comes from multiple systems and have numerous problems that prevent a quick and straightforward analysis.  There are duplicate rows but not in the traditional easy sense.  The duplicates only exist across certain columns making the dataset longer than it needs to be.  It takes a creative approach to figure out how to parse.  There are also problems with data integrity such that the same episode_id has different patient numbers depending on the system the data came from.  This must be corrected or the results will be skewed as the model may not consider a group of events as related to one patient and therefore not learn correctly.  There are other issues where dates don't make sense.  For example, a discharge, date later than the initial start of care date.  The list goes on and on.

With the data integrity issues in mind, I felt the most valuable approach was to build a scaffolding so that modeling might be easier to replicate in the future.  This framework had me conceptualize the data into four main clusters.

Patients <br/>
Episodes - 60 day periods which may result in numerous visits by medical professionals <br/>
Visits - An actual provider interviewing and observing the patient, and documenting findings according to OASIS standards. <br/>
Events - The actual observations which may be behavioral, lab results, or questionaires to the patients <br/>

By splitting the data into these 4 separate dataframes/tables it makes a more structured analysis possible.

## Weaknesses in the Data

### Data Proccesssng Approach

In addition to the previously mentioned high-level data integrity concerns, the effectiveness of a mortality prediction model/algorithm is directly contingent upon the quality of features representing the data. Given that we initially were provided up to 250 features to work with it was imperative to perform some feature selection to not only eliminate any redundancies but also ensure the information contained would not skew the model output.

Since we are working with OASIS data many of the features are structured in a standardized way, a typical example is: "1 - Yes, the patient is experincing x", "0 - No, the patient is not y".  This strucutre allows us extract the integer away from the entire string so the model will receive a simple integer input.  For other categorical factors that are missing the integer and have Yes/No we can simply convert them to integers and in the case of string only information, it is almost always limited to 6 or fewer possible responses so therefore also possible to convert to integers.

Since all of the features are dependent on actual human health care providers to collect, there are certain items that seem to be more prevalent across the patients.  For example, almost every patient has their height and weight calculated, but some of the more obscure questions are largely blank.  In this light we looked at which features most patients in both classes had in common and priortized those.  We need to be careful in that it is certainly possible for patients who died quickly to have features, that patients who lived longer might not have, so its not simply eliminating features with alot of N/A rows.  More thought and analysis in selecting which features to keep is warranted.

# Model Chosen

The mortality prediction task can be approached in many different ways according to the objectives and the type of data provided.  I wanted to try to challenge myself a bit so I chose to implement a deep learning model and try to see if I could get my GPU involved on my local machine.  Given that the dataset provided has several time/date components of critical importance each patient can be viewed as a distinct entity that is subject to a sequence of events.  These events are episiodes which are 60 day time periods used to manage patient care and observe.  There are additional sequences of Health Care provider visits in which observations are collected.

I chose to implement a long short-term memory (LSTM) model as it was a specifically developed recurrent neural net designed to address the challenges of time-series data. By feeding the model chronological episodic visit data, the order of the events that occur to any patient become significant predictors.  LSTM models are uniquely compatible for mortality prediction because they 'remember' the sequential occurence of events and find patterns over time. Contrast this with more simplistic models which will simply look at ALL the event that have happened to a specific patient in a specific time period without considering the chronology.


# Results

# Conclusion - Next Steps
