from multiprocessing.sharedctypes import Value
import os
import datetime as dt
from time import strptime, tzname
from tkinter import E, N
from xmlrpc.client import DateTime
from dateutil import parser
import pandas as pd
import sys
import logging
from dateutil.relativedelta import *
from dateutil import tz

class Outcome:
    def __init__(self,call_outcome,meaning,resting_rule):
        self.call_outcome = call_outcome
        self.meaning = meaning
        self.resting_rule = resting_rule

    def __contains__(self,call_outcome):
        if call_outcome == self.call_outcome:
            return True
        return False
    
    def get_rule(self):
        return self.resting_rule

class Outcomes:
    def __init__(self):
        self.rules = {}
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(filename='config.log',encoding='utf-8',level=logging.DEBUG)
        self.create_rules()
        
    def create_rules(self):
        try:
            rules_path = os.path.join(os.getcwd(),'rules.txt')
            if os.path.isfile(rules_path):
                self.create_rules_from_file(rules_path)
            else:
                self.create_rules_hardcoded()

        except Exception as exc:
            self.logger.exception(exc)

    def create_rules_hardcoded(self):
        self.rules['Hung Up'] = Outcome("Hung Up","The prospective customer just hung up on the agent during the call","6 months")
        self.rules['Wrong number'] = Outcome("Wrong number","The number that was dialled was incorrect","Permanent")
        self.rules['Decision maker unavailable'] = Outcome("Decision maker unavailable","The key person that the agent needed to speak to was unavailable perhaps due to sickness, or being on holiday","Do not rest")
        self.rules['Callback'] = Outcome("Callback","A follow-up call has been scheduled with the customer","Do not rest")
        self.rules['Not Interested'] = Outcome("Not Interested","The prospective customer was not interested in our client’s service at this time","3 months")
        self.rules['Engaged'] = Outcome("Engaged","The agent could not get through to the prospective client","Do not rest")
        
    def create_rules_from_file(self,rules_file):
        try:
            with open(rules_file,'r') as file:
                    rule = file.readline()
                    #must be the header row
                    if 'Call Outcome' in rule:
                        rule = file.readline()
                    while rule != "":
                        rule_details = rule.split('|')
                        if len(rule_details) == 3:
                            new_outcome = Outcome(*rule_details)
                            if new_outcome.call_outcome not in self.rules:
                                self.rules[new_outcome.call_outcome] = new_outcome
                            else:
                                self.logger.debug(f"call outcome clash! {new_outcome.call_outcome} already exists in rules")
                        else:
                            self.logger.debug('Problem with rule line, needs 3 fields!')
                        rule_details = None
                        rule = file.readline()             
        except Exception as exc:
            self.logger.exception(f'Error when parsing rules file: {exc}')
    
    def return_rule(self,call_outcome):
        if call_outcome in self.rules:
            return self.rules[call_outcome].get_rule()
        else:
            self.logger.exception(f"{call_outcome}, couldn't find matching rule!")
        return ""


class LeadParser():
    def __init__(self):
        self.data_files_location = ""
        self.returns_due_datetime = None
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(filename=f'{dt.datetime.utcnow().strftime("%d_%m_%Y")} app.log',encoding='utf-8',level=logging.DEBUG)
        self.call_outcomes = Outcomes()
    
    def validate_inputs(self,args):
        validation_messages = ""
        #check we have been given a directory
        if not os.path.isdir(args[0]):
            validation_messages += f"{args[0]} is not a valid directory \n"
        #using list comprehension to formulate a list of files in the given directory that are actually csv files.
        elif len([f for f in os.listdir(args[0]) if '.csv' in f]) == 0:
            validation_messages += f"{args[0]} does not contain any csv files!\n"
        if args[1] == "":
            validation_messages += f"{args[1]} is empty!"
            return validation_messages

        try:
            #just try parse the datetime in this format, will throw an error if a value is invalid for its position,
            #but won't if you have entered the date in the wrong format (m/d/y) and the values are still valid, like 01/02/2022 (Jan 1st)
            dt.datetime.strptime(args[1],'%d/%m/%Y')
        except ValueError as ve:
            #self.logger.exception(ve)
            validation_messages += "Encountered a value error with the inputted date, please make sure it conforms to application specification\n"
        except Exception as exc:
            self.logger.exception(exc)
            validation_messages += " Error with lead return date input value, please check format.\n"
        
        return validation_messages
    
    def set_inputs(self,args):
        try:
            self.logger.debug(args[0])
            self.logger.debug(args[1])
            self.data_files_location = args[0] 
            self.returns_due_datetime = dt.datetime.strptime(args[1],'%d/%m/%Y')
            return True
        except Exception as exc:
            self.logger.exception(exc)
            return False
    
    #returns csv file
    def process_files(self):
        lead_ids = []
        #set up outcome rules
        try:
            for file in os.listdir(self.data_files_location):
                if '.csv' in file:
                    #get the csv data as a dataframe
                    df = self.ingest(os.path.join(self.data_files_location,file))

                    #if none is returned then we exit out.
                    if type(df) == type(pd.DataFrame()):
                        if df.empty:
                            print(f"Failed to parse {file}")
                            continue
                    else:
                        print(f"Failed to parse {file}")
                        continue

                    #apply filtering rules
                    ids = self.filter(df)
                    lead_ids.extend(ids)

            csv_file = ""
            if len(lead_ids) > 0:
                csv_file = self.create_csv(lead_ids)
            else:
                print("no leads to output into a csv!")
            return csv_file
        except Exception as exc:
            print("Exception detected during file processing, please check logs for more information.")
            self.logger.exception(exc)
            return ""

    #returns same datestring, or one that has been manipulated by rest rule, or empty if perm resting rule
    def process_call_outcome(self,call_outcome,call_occurred):
        rule = self.call_outcomes.return_rule(call_outcome)
        return_datetime = ""

        #process the call_occurred
        if 'months' in rule:
            #need to apply the month addition
            return_datetime =  self.process_month_addition_rules(call_occurred,rule)
        elif 'Do not rest' in rule:
            return_datetime = call_occurred
        
        return return_datetime
    
    def is_lead_rested(self,lead_date):
        try:
            #this format is not the format in the pdf, but rather in the sample data given!
            target_format = '%d/%m/%Y %H:%M:%S'
            lead_datetime = dt.datetime.strptime(lead_date,target_format)
            self.logger.debug(f"leads sent out {self.returns_due_datetime} and this lead is available {lead_datetime}")
            if self.returns_due_datetime >= lead_datetime:
                self.logger.debug(f"detected as sendable")
                return True

        except Exception as exc:
            self.logger.exception(exc)
        return False

    def process_contract_renewal(self,renewal_date):
        #convert renewal date into datetime obj
        #compare renewal date against deliver date
        target_format = '%Y/%m/%d'
        process_lead = False
        try:
            renewal_date_dt = dt.datetime.strptime(renewal_date,target_format)
            delivery_date_boundary = self.returns_due_datetime + relativedelta(months=-3)
            if renewal_date_dt <= self.returns_due_datetime and renewal_date_dt >= delivery_date_boundary:
                self.logger.debug("contract within 3 months of delivery date")
                process_lead = True
        except Exception as exc:
            self.logger.exception(exc)

        return process_lead

    #processes the lead based on whether its contract renewal, or based on call_outcome rule.
    def process_lead(self,call_outcome,call_occurred,contract_renewal_date):
        lead_needs_processing = False
        if contract_renewal_date != "nan":
                lead_needs_processing = self.process_contract_renewal(contract_renewal_date)
        else:
            lead_date_str = self.process_call_outcome(call_outcome,call_occurred)
            #perm call outcome, or error
            if lead_date_str == "":
                lead_needs_processing = False
            #this would mean that there was no processing on the date string because its do not rest.
            elif lead_date_str == call_occurred:
                lead_needs_processing = True
            #else would mean the datetime str has been incremented, or more specifically rested.
            else:
                #now we need to check whether the date we are sending the leads out, is greater than the rested time, ie we have rested enough.
                lead_needs_processing = self.is_lead_rested(lead_date_str)
        return lead_needs_processing


    #apply string to datetime, then add months, then return as string again.
    def process_month_addition_rules(self,call_occurred,rule):
        try:
            #this format is not the format in the pdf, but rather in the sample data given!
            target_format = '%d/%m/%Y %H:%M:%S'
            call_as_datetime = dt.datetime.strptime(call_occurred,target_format)

            #months comes as 6 months or 3 months, so we strip out the text and cast to int
            num_of_months = int(rule.replace(' months',''))

            #using dateutil.relativedelta to simply increase date by a set number of months
            call_as_datetime += relativedelta(months=+num_of_months)

            #convert back to string and fire back
            return call_as_datetime.strftime(target_format)
        except Exception as exc:
            self.logger.exception(exc)

    #creates a data frame from the passed in csv file.
    def ingest(self, filename):
        print(f"Attempting ingesting {filename}")
        #check we have a valid file, could just try parse, but this will give us better error reporting for the user. 
        if not os.path.isfile(filename):
            print("Failed to ingest file, was not detected as a proper file")
            return None

        try:
            #return the data frame created by the read_csv function
            df = pd.read_csv(filename)
            #check we have all the right columns, could pick up a rogue file!
            for col in ['Call ID','Lead ID','Call Datetime','Call Outcome','Contract Renewal Date']:
                if col not in df:
                    return None
            print(f"Ingested {filename}")
            return df
        except Exception as exc:
            print(f"Failed to parse file: {exc}")
            return None

    #filters out the data
    def filter(self, data_frame):
        ids = {}

        for index,series in data_frame.iterrows():
            lead_needs_processing = False
            #case to string as we will use it in a dict for fast lookup
            lead_id = str(series[0])
            call_outcome = series[3]
            call_occurred = series[2]
            contract_renewal_date = str(series[4])

            lead_needs_processing = self.process_lead(call_outcome,call_occurred,contract_renewal_date)
            
            #if the lead_id is already in there, then we overwrite what its last status was.
            ids[lead_id] = lead_needs_processing
        lead_ids = [id[0] for id in ids.items() if id[1]]
        print("Applied Filtering")
        return lead_ids

    #creates a csv file from data_frame, and returns the path to that file.
    def create_csv(self, lead_ids):
        print("Creating CSV")
        local_dir = os.getcwd()
        target_file_name = f"{self.returns_due_datetime.strftime('%d_%m_%Y')} leads.csv"
        full_csv_path = os.path.join(local_dir,target_file_name)
        if os.path.isfile(full_csv_path):
            print(f"Lead file already exists! {target_file_name}")
            print(f"Do you wish to overwrite this file? Y/N")
            answer = input().lower()
            if answer == 'n':
                print("exiting csv creation")
                return ""
            else:
                os.remove(full_csv_path)
        try:
            with open(full_csv_path,'x') as csv_leads:
                csv_leads.write('Lead ID \n')
                for id in lead_ids:
                    csv_leads.write(str(id) + '\n')
                csv_leads.close()
        except Exception as exc:
            full_csv_path = ""
            print(exc)
            self.logger.exception(exc)
            
        return full_csv_path
    

#input = path to directory, date that leads will be sent back to client
def main(args):
    #check we have the 2 arguements required
    print(len(args))
    if len(args) != 2:
        print("Input requires '"'path to dialling data'"' '"'date leads will be sent back to client'"'")
        #for testing
        return "Input requires [path to dialling data], [date leads will be sent back to client]\n"
    
    lead_parser = LeadParser()
    #if validation fails, then exit out
    messages = lead_parser.validate_inputs(args)
    if messages != "":
        print(messages)
        return messages

    #application shouldn't really exit here, as we have already validated the inputs, but just to be on the safe side!
    if not lead_parser.set_inputs(args):
        print("failed")
        return ""

    csv_file = lead_parser.process_files()
    print(f"Your leads file is {csv_file}")

    return csv_file

#entry point for the application
if __name__ == '__main__':
    #take out the calling name
    #main(sys.argv[1:])
    main([r'C:\Users\tkk10\Documents\Development\Growth Intelligence','01/08/2022'])
    
    
    