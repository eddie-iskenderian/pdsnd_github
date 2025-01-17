### Date created
4th of July 2022

### Project Title
Interactive BikeShare Statistics Explorer

### Description
An interactive program for exploring BikeShare data. Run the following command in the terminal
to start the program.
  python3 bikeshare.py

When the script is executed, you will be prompted to select the time filter for the statistics
that will be displayed. An example of the prompt and user responses is shown below. Note that you can
enter the full name of a city, month or day. Otherwise, you can enter the abbreviation.

```
Hello! Let's explore some US bikeshare data!
---------------------------------------------

Would you like to see data for Chicago [C], New York City [NYC] or Washington [W]?
> C

Would you like to filter the data by month [m], day [d] or not at all [none]?
> d

Which day - Monday [M], Tuesday [Tu], Wednesday [W], Thursday [Th], Friday [F], Saturday [Sa], Sunday [Su] or all [all]?
> Tu
```

Sample statistics include:
```
Showing statistics for Chicago
-------------------------------

Loading data...
                      
Calculating The Most Frequent Times of Travel...
                      
The most popular month of departure is June.

The most popular day of departure is Tuesday.

The most common hour of departure is 5pm

This took 0.016842126846313477 seconds.
------------------------------------------------

Would you like to view the raw data?
> yes
Start Time
2017-06-23 15:09:32
2017-05-25 18:19:03
2017-01-04 08:27:49
2017-03-06 13:49:38
2017-01-17 14:53:07
```

### Files used
README.md
bikeshare.py

### Credits
https://stackoverflow.com/questions/287871/how-do-i-print-colored-text-to-the-terminal
This site was referenced for printing coloured text in the terminal

https://www.geeksforgeeks.org/start-and-stop-a-thread-in-python/
This site was referenced for threading in Python

https://itnext.io/overwrite-previously-printed-lines-4218a9563527
This site was referenced for the animated wait spinner

