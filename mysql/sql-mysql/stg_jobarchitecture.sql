CREATE TABLE stg_jobarchitecture (
    firstname varchar(255),
    lastname varchar(255),
    employeenumber int Primary Key,
    attrition boolean,
    jobdirect varchar(255),
    joblevel varchar(255),
    numcompaniesworked int, 
    totalworkingyears int, 
    yearsatcompany int, 
    yearsincurrentrole int, 
    yearssincelastpromotion int, 
    yearswithcurrmanager int, 
    jobtitle varchar(255)
);