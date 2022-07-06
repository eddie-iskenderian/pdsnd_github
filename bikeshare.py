import os
from os.path import isfile
import time
import pandas as pd
from threading import Thread

def is_csv_file(file):
    """Determines whether a file is a CSV file by the file extension"""
    return isfile(file) and file[-4:] == '.csv'

def get_city_name(csv_name):
    """
    Derives the name of the city based on the name of a CSV file

    Args:
        (str) csv_name - The name of the CSV file containing a city's data

    Returns:
        (str) The human readable name of the corresponding city
    """
    return csv_name[:-4].replace('_', ' ').title()

def get_csv_name(city):
    """
    Derives the name of the city's CSV data file based on the name of the city

    Args:
        (str) city - The human readable name of a city

    Returns:
        (str) The name of the CSV file containing the city's data
    """
    return '{}.csv'.format(city.replace(' ', '_').lower())

ACRONYMN = 0
PROPER_NAME = 1

def abbreviate_initial(city):
    """
    Abbreviate the name of the city using its initials.

    Args:
        (str) city - The name of a city.

    Returns:
        (str) The abbreviation of the city name.
    """
    parts = city.split(' ')
    initials = ''.join([part[0] for part in parts])
    return initials

def generate_city_prompts(cities):
    """
    Create prompts for a list of cities. Each prompt will include the city and its abbreviation.
    Abbreviations are created for each name by extracting the city's initials in uppercase.

    Args:
        (list) cities - A list of city names for which to create prompts.

    Returns:
        (list) prompts - A list of prompts, each including the name of a city and its abbreviation
        (dict) abbreviations - A mapping of cities by their abbreviations
    """
    abbreviations = {}
    prompts = []
    for city in cities:
        abbreviation = abbreviate_initial(city)
        abbreviations[abbreviation] = city
        # Create a prompt from the city name its abbreviation.
        prompts.append('{} [{}]'.format(city, abbreviation))
    return prompts, abbreviations

def generate_name_prompts(names):
    """
    Create prompts for a list of names. Each prompt will include the name and its abbreviation.
    Abbreviations are created for each name by truncating the name to it's shortest unique left component
    across all names.

    Args:
        (list) names - A list of names for which to create prompts.

    Returns:
        (list) prompts - A list of prompts, each including a name and its abbreviation.
        (dict) abbreviations - A mapping of names by their abbreviations.
    """
    potential_abbreviations = {}
    for name in names:
        # Capture a 'catch all' option
        if name.find('not') != -1:
            potential_abbreviations['none'] = name
            continue
        elif name.find('all') != -1:
            potential_abbreviations['all'] = name
            continue
        # Build up the abbreviation of the word until a unique abbreviation is found, thus far
        for length in range(1, len(name) + 1):
            first_part = name[:length]
            if not first_part in potential_abbreviations:
                # No clash
                potential_abbreviations[first_part] = name
                break
            else:
                # A clash was found
                previous_name = potential_abbreviations[first_part]
                if not previous_name == None:
                    # Mark the duplicate abbreviation and update it with the next potential on for that word
                    potential_abbreviations[first_part] = None
                    potential_abbreviations[previous_name[:length + 1]] = previous_name
    # Generate the prompts and mapping of abbreviations to their corresponding name
    abbreviations = {}
    abbreviation_map = {}
    for key, value in potential_abbreviations.items():
        if not value == None:
            abbreviations[key] = value
            abbreviation_map[value] = key
    prompts = ['{} [{}]'.format(name, abbreviation_map[name]) for name in names]

    return prompts, abbreviations

def build_options(names, abbreviation_type):
    """
    Build the prompt options derived from the list of names to filter upon,
    and their abbreviations.

    Args:
        (list) names - The names of the entities on which to filter
        (int) abbreviation_type - The type of abbreviation to produce
                    ACRONYMN or PROPER_NAME
    Returns:
        (str) options - The options to choose from that will be displayed in the prompt.`
        (dict) abbreviations - A mapping of names by their abbreviations.
    """
    if abbreviation_type == ACRONYMN:
        # A list of city names has been supplied
        prompts, abbreviations = generate_city_prompts(names)
    else:
        # A list of names has been supplied
        prompts, abbreviations = generate_name_prompts(names)
    if len(prompts) == 1:
        city_part = prompts[0]
    else:
        # String the options together
        first = prompts[:-1]
        first_part = ', '.join(first)
        last = prompts[-1]
        options = ' or '.join([first_part, last])
    return options, abbreviations

# https://stackoverflow.com/questions/287871/how-do-i-print-colored-text-to-the-terminal
TC_HEADER = '\033[95m'
TC_OKBLUE = '\033[94m'
TC_OKCYAN = '\033[96m'
TC_OKGREEN = '\033[0;32m'
TC_WARNING = '\033[93m'
TC_FAIL = '\033[91m'
TC_ENDC = '\033[0m'

def colour(string, terminal_colour):
    """
    Apply a colour to a string for display in the terminal
    
    Args:
        (str) string - The sting to colour
        (str) terminal_colour - The colour to apply

    Returns:
        The string with the colour applied
    """
    return '{}{}{}'.format(terminal_colour, string, TC_ENDC)

def show_prompt(names, abbreviation_type, beginning):
    """
    Display a prompt for selecting option.

    Args:
        (str) beginning - The beginning of the prompt to display.
        (list) names - The source of the options to select.
        (int) abbreviation_type - The type of abbreviation to produce
                    ACRONYMN or PROPER_NAME
    Returns:
        (str) The response made to the prompt.
    """
    word_part, prompt_map = build_options(names, abbreviation_type)
    # Prompt a maximum of 3 times
    MAX_PROMPTS = 3
    for index in range(0, MAX_PROMPTS):
        raw = input(colour('\n{} {}?\n> '.format(beginning, word_part), TC_OKCYAN))
        selected = None
        for key, value in prompt_map.items():
            lowercase = raw.lower()
            if lowercase == key.lower() or lowercase == value.lower():
                selected = value
                break
        if selected is not None:
            break
    if selected is None:
        raise Exception('Invalid selection: {}'.format(raw or "''"))
    return selected

def create_city_csv_list(project_path):
    """
    Create a mapping of city names to their corresponding CSV file name

    Args:
        (str) project_path - The path to the data files.

    Returns:
        list(str) The names of the CSV files found.
    """
    csv_files = [file for file in os.listdir(project_path) if is_csv_file(file)]
    return csv_files

WEEKDAYS = ['Monday','Tuesday','Wednesday','Thursday','Friday', 'Saturday', 'Sunday', 'all']
MONTHS = ['January','February','March','April','May', 'June', 'all']
ALL = -1

def get_filters(dataset, project_path):
    """
    Asks user to specify a city, month, and day to analyze. Cities are mapped to
    the name of the CSV containing their dataset.

    Args:
        (str) dataset - The name of the dataset
        (str) project_path - The path to the data

    Returns:
        (str) csv - The name of the csv file to analyze.
        (str) month - The name of the month to filter by, or "all" to apply no month filter.
        None if filtering by day.
        (str) day - The name of the day of week to filter by, or "all" to apply no day filter
        None if filtering by month.
    """
    welcome_message = '\nHello! Let\'s explore some {} data!'.format(dataset)
    print(colour(welcome_message, TC_HEADER))
    print(colour('-' * len(welcome_message), TC_HEADER))
    # Get the selection for the city.
    city_csv_files = create_city_csv_list(project_path)
    if len(city_csv_files) == 0:
        raise Exception('No CSVs containing statistical data for a city were found')
    cities = [get_city_name(csv) for csv in city_csv_files]
    city = show_prompt(cities, ACRONYMN, 'Would you like to see data for')
    # Choose the method of date filtering
    date_filter = show_prompt(['month', 'day', 'not at all'], PROPER_NAME, 'Would you like to filter the data by')

    stats_header = '\nShowing statistics for {}'.format(city)
    month, day = ALL, ALL
    if date_filter == 'month':
        # Filtering by month.
        # Choose the month to filter by.
        month_name = show_prompt(
            MONTHS,
            PROPER_NAME,
            'Which month -'
        )
        if month_name != 'all':
            month = MONTHS.index(month_name) + 1
            stats_header = '{} in the month of {}'.format(stats_header, month_name)

    elif date_filter == 'day':
        # Filtering by day.
        # Choose the day to filter by.
        day_name = show_prompt(
            WEEKDAYS,
            PROPER_NAME,
            'Which day -'
        )
        if day_name != 'all':
            day = WEEKDAYS.index(day_name)
            stats_header = '{} on {}s'.format(stats_header, day_name)

    print(colour(stats_header, TC_HEADER))
    print(colour('-' * len(stats_header), TC_HEADER))
    return get_csv_name(city), month, day


# Create a thread to display a progress prompt
# https://www.geeksforgeeks.org/start-and-stop-a-thread-in-python/
wait, thread, kill = False, None, False

def stop_waiting(kill_thread=False):
    """
    Stop the thread used to render the progress prompt

    Args:
        (boolean) kill_thread - Kill the thread immediately
    """
    global wait
    global thread
    global kill
    wait = False
    kill = kill_thread
    if not thread is None:
        thread.join()
        thread = None
    kill = False

def show_on_wait():
    """
    Create a thread that will display a progress indicator on a timer.
    By default the indicator will finish its cycle before it terminates.
    """
    def run(arg):
        global wait
        global kill
        min_intervals = 48
        max_intervals = 48
        max_chars = 20
        highlight = 'oooo'
        for i in range(max_intervals):
            if kill or (not wait and i >= min_intervals):
                break
            time.sleep(0.1)
            highlight_length = len(highlight)
            iteration = i % (max_chars + highlight_length)
            left = iteration - highlight_length
            right = iteration

            # The number of dots to the left of the highlight
            num_left = max(left, 0)
            # The length of the highlight
            num_highlights = min(max_chars, right) - max(0, left)
            # The number of dots to the right of the highlight
            num_right = max_chars - (num_left + num_highlights)
            print(colour(' {}{}{}\r'.format('.' * num_left, highlight[:num_highlights], '.' * num_right), TC_OKCYAN), end='')
        wait = False
        print(' ' * (max_chars + 2), end='')

    # Start the progress indicator 
    global wait
    global thread
    wait = True
    thread = Thread(target = run, args =(10, ))
    thread.start()

# The name of time columns
HOUR_COLUMN = 'hour'
WEEKDAY_COLUMN = 'day_of_week'
MONTH_COLUMN = 'month'
GENDER_COLUMN = 'Gender'
DOB_COLUMN = 'Birth Year'
USER_COLUMN = 'User Type'

def filter_by_time(df, column, selected):
    """
    Applies a time filter to a Pandas data frame
    Args:
        (pandas.DataFrame) df - The data frame to filter
        (str) column - The column to drop as a result of applying the filter
        (str) selected - The selected period on which to filter
    
    Returns:
        The filtered data frame
    """
    if selected != ALL:
        df = df[df[column] == selected]
        df.drop(columns=column, inplace=True)
    return df

def load_data(csv, month, day):
    """
    Loads data from the specified city CSV file and filter by month and day if applicable.

    Args:
        (str) csv - The name of the CSV file to analyze
        (str) month - The index of the month, starting at 1 for Jan, to filter by,
                      or -1 to apply no month filter.
        (str) day - index of the day of week, starting at 0 for Monday, to filter by,
                    or -1 to apply no day filter
    Returns:
        df - Pandas DataFrame containing city data filtered by month and day
    """
    print(colour('\nLoading data...', TC_OKCYAN))
    show_on_wait()
    # Load data file for the selected city into a dataframe
    df = pd.read_csv(csv)

    # Convert the Start Time column to datetime
    df['Start Time'] = pd.to_datetime(df['Start Time'])

    # Extract month and day of week from Start Time to create new columns
    df[MONTH_COLUMN] = df['Start Time'].dt.month
    df[WEEKDAY_COLUMN] = df['Start Time'].dt.dayofweek
    df[HOUR_COLUMN] = df['Start Time'].dt.hour

    # Filter by the seleted time frame
    df = filter_by_time(df, MONTH_COLUMN, month)
    df = filter_by_time(df, WEEKDAY_COLUMN, day)
    stop_waiting()
    return df

def time_stats(df):
    """Displays statistics on the most frequent times of travel."""

    notice = 'Calculating The Most Frequent Times of Travel...'
    print(colour('\n{}'.format(notice), TC_OKCYAN))
    start_time = time.time()

    output = []
    show_on_wait()
    # display the most common month
    if MONTH_COLUMN in df.columns:
        month_index = df[MONTH_COLUMN].mode()[0]
        month = MONTHS[month_index - 1]
        output.append('\nThe most popular month of departure is {}.'.format(month))

    # display the most common day of week
    if WEEKDAY_COLUMN in df.columns:
        weekday_index = df[WEEKDAY_COLUMN].mode()[0]
        weekday = WEEKDAYS[weekday_index]
        output.append('\nThe most popular day of departure is {}.'.format(weekday))

    # display the most common start hour
    hour = df[HOUR_COLUMN].mode()[0]
    hour_label = hour % 12 or '12'
    hour_string = '{}{}'.format(hour_label, 'am' if hour < 12 else 'pm')
    output.append('\nThe most common hour of departure is {}'.format(hour_string))

    output.append("\nThis took %s seconds." % (time.time() - start_time))
    stop_waiting()
    print(colour('\n'.join(output), TC_OKCYAN))
    print(colour('-' * len(notice), TC_OKCYAN))
    prompt_for_raw_stats(df.filter(['Start Time'], axis=1))
    print(colour('-' * len(notice), TC_OKCYAN))

def station_stats(df):
    """Displays statistics on the most popular stations and trip."""

    notice = 'Calculating The Most Popular Stations and Trip...'
    print(colour('\n{}'.format(notice), TC_OKCYAN))
    start_time = time.time()

    output = []
    show_on_wait()
    # display most commonly used start station
    output.append('\nThe most commonly used start station is {}'.format(df['Start Station'].mode()[0]))

    # display most commonly used end station
    output.append('\nThe most commonly used end station is {}'.format(df['End Station'].mode()[0]))

    # display most frequent combination of start station and end station trip
    df['start_to_end_trip'] = df['Start Station'] + ' to ' +  df['End Station']
    output.append('\nThe most frequent combination of start station and end station trip is {}'
        .format(df['start_to_end_trip'].mode()[0]))
    output.append("\nThis took %s seconds." % (time.time() - start_time))
    stop_waiting()
    print(colour('\n'.join(output), TC_OKCYAN))
    print(colour('-' * len(notice), TC_OKCYAN))
    prompt_for_raw_stats(df[['Start Station', 'End Station']])
    print(colour('-' * len(notice), TC_OKCYAN))

def trip_duration_stats(df):
    """Displays statistics on the total and average trip duration."""

    notice = 'Calculating Trip Duration...'
    print(colour('\n{}'.format(notice), TC_OKCYAN))
    start_time = time.time()

    output = []
    show_on_wait()
    # display total travel time
    output.append('\nThe total travel time is {} seconds'.format(round(df['Trip Duration'].sum())))

    # display mean travel time
    output.append('\nThe mean travel time is {} seconds'.format(round(df['Trip Duration'].mean())))

    output.append("\nThis took %s seconds." % (time.time() - start_time))
    stop_waiting()
    print(colour('\n'.join(output), TC_OKCYAN))
    print(colour('-' * len(notice), TC_OKCYAN))
    prompt_for_raw_stats(df[['Trip Duration']])
    print(colour('-' * len(notice), TC_OKCYAN))

def user_stats(df):
    """Displays statistics on bikeshare users."""

    notice = 'Calculating User Stats...'
    print(colour('\n{}'.format(notice), TC_OKCYAN))
    start_time = time.time()

    output = []
    show_on_wait()
    # Display counts of user types
    value_counts = df[USER_COLUMN].value_counts()
    kinds = value_counts.index.tolist()
    columns_to_show_raw_data = [USER_COLUMN]
    output.append('\nCounts of user types\n')
    output += ['{}: {}'.format(kind, value_counts[kind]) for kind in kinds]

    # Display counts of gender
    if GENDER_COLUMN in df.columns:
        value_counts = df[GENDER_COLUMN].value_counts()
        kinds = value_counts.index.tolist()
        output.append('\nCounts of genders\n')
        output += ['{}: {}'.format(kind, value_counts[kind]) for kind in kinds]
        columns_to_show_raw_data.append(GENDER_COLUMN)

    # Display earliest, most recent, and most common year of birth
    if DOB_COLUMN in df.columns:
        dobs = df[DOB_COLUMN].dropna(axis = 0).astype(int)
        value_counts = dobs.value_counts()
        kinds = value_counts.index.tolist()
        output.append('\nCounts of year of birth\n')
        output += ['{}: {}'.format(kind, value_counts[kind]) for kind in kinds]
        columns_to_show_raw_data.append(DOB_COLUMN)

    output.append("\nThis took %s seconds." % (time.time() - start_time))
    stop_waiting()
    print(colour('\n'.join(output), TC_OKCYAN))
    print(colour('-' * len(notice), TC_OKCYAN))
    prompt_for_raw_stats(df[columns_to_show_raw_data])
    print(colour('-' * len(notice), TC_OKCYAN))

def prompt_for_raw_stats(df):
    """Prompts the user for more stats"""
    max_rows = 25
    row = 0
    row_count = 5
    display_data = input(colour('\nWould you like to view the raw data?\n> ', TC_HEADER))
    if display_data.lower() == 'yes':
        while row < max_rows and row < len(df.index):
            indices = df.index[row:min(row + row_count + 1, len(df.index)) - 1]
            print(colour(df.loc[indices].to_string(index=False), TC_OKGREEN))
            row += row_count
            display_more_data = input(colour('Would you like to view more raw data?\n> ', TC_HEADER))
            if not display_more_data.lower() == 'yes':
                break

def main():
    while True:
        dataset = 'US bikeshare'
        path = '.'

        try:
            # Prompt the user for their choice of filters
            csv, month, day = get_filters(dataset, path)
            # Load the data based on the interactive selections
            df = load_data(csv, month, day)
            # Calculate and display the statistics
            time_stats(df)
            station_stats(df)
            trip_duration_stats(df)
            user_stats(df)
        except (EOFError, KeyboardInterrupt) as input_exp:
            stop_waiting(True)
            print('\nBye!')
            break
        except Exception as e:
            stop_waiting(True)
            print(str(e))

        try:
            restart = input('\nWould you like to restart? Enter yes or no.\n> ')
            if restart.lower() != 'yes':
                break
        except:
            print('\nBye!')
            break

if __name__ == "__main__":
    main()
