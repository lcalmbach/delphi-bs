update bevoelkerung set altersklasse_jung_alt = 'x 0-17 Jährige' where person_alter <18;
update bevoelkerung set altersklasse_jung_alt = 'x 18-64 Jährige' where person_alter between 18 and 64;
update bevoelkerung set altersklasse_jung_alt = 'x 65+ Jährige' where person_alter > 64;

update bevoelkerung set altersklasse_10 = 'x 0-9 Jährige' where person_alter <10;
update bevoelkerung set altersklasse_10 = 'x 10-19 Jährige' where person_alter between 10 and 19;
update bevoelkerung set altersklasse_10 = 'x 20-29 Jährige' where person_alter between 20 and 29;
update bevoelkerung set altersklasse_10 = 'x 30-39 Jährige' where person_alter between 30 and 39;
update bevoelkerung set altersklasse_10 = 'x 40-49 Jährige' where person_alter between 40 and 49;
update bevoelkerung set altersklasse_10 = 'x 50-59 Jährige' where person_alter between 50 and 59;
update bevoelkerung set altersklasse_10 = 'x 60-69 Jährige' where person_alter between 60 and 69;
update bevoelkerung set altersklasse_10 = 'x 70-79 Jährige' where person_alter between 70 and 79;
update bevoelkerung set altersklasse_10 = 'x 80-89 Jährige' where person_alter between 80 and 89;
update bevoelkerung set altersklasse_10 = 'x 90-99 Jährige' where person_alter between 90 and 99;
update bevoelkerung set altersklasse_10 = 'x >100 Jährige' where person_alter between 10 and 19;