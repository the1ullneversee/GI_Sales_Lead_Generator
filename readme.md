<h1> Welcome to the Sales Lead Generator </h1>
<h4> Instructions </h4>
<p> The supplied application files contain both a Pipfile and requirements.txt for downloading of neccessary modules. It is recommended that either is run before invoking the application. </p>
<p> Application can be invoked by running application.py, and requires two arguements:
<li> Data File Location: <small> Location to the data files containing the telemarketing activity </small> </li>
<li> date that the Leads will be sent back to the client: <small> format must be 'd-m-y'</small> </li>

<h4> Application Assumptions </h4>
<p> The application assumes that the data files datetime fields follow the format of 'DD/MM/YYYY HH:MM:SS' this is contrary to the format given in the instructions as 'YYYY-MM-DD HH:MM:SS', reason being is that the sample data is in the UK format.

<p> The application also assumes that all files given by the data file location, will be outputted into a singular csv file. The alternative is to output each input file into a csv file, which can be changed very easily.</p>

<p> The application also comes with a rules.txt configuration file, with delimeter '|'. The purpose of this file is to extend the functionality of the rules that govern call outcomes. If the file is not present, the application will use hardcoded rules! </p>

<p> The applicaition also has a testing file, which can be ran using pytest tests.py along with diagnostic log files generated in the local folder during each application run. If you encounter an exception, it should be logged in the .log file.</p>

