import curses
from curses import wrapper
from winsound import PlaySound, SND_FILENAME
from time import sleep, strftime, gmtime
from json import load, dump

from fomodoro.utils import States, TIME_FORMAT, INFO_FILE, BELL_SOUND_FILE
from fomodoro.stopwatch import Stopwatch
from fomodoro.timer import Timer
from fomodoro.stats import add_stopwatch_record, add_timer_record


stopwatch_obj = Stopwatch()
timer_obj = Timer()

def main(stdscr) -> None: # pylint: disable=missing-function-docstring
    curses.resize_term(7, 40)
    time_window = curses.newwin(1, 9, 1, 16)

    with open(INFO_FILE, 'r', encoding='utf-8') as info_file:
        info = load(info_file)

    if info["stopwatch_state"] == States.WITHOUT_START.value: # Stopwatch
        stopwatch_obj.start()
        stopwatch_obj.elapsed_seconds = info["elapsed_seconds"]

        stdscr.clear()
        stdscr.addstr(3, 5, "Instructions:\n")
        stdscr.addstr(4, 3, "- Press p to pause the stopwatch.\n")
        stdscr.addstr(5, 3, "- Press s to stop the stopwatch.")
        stdscr.refresh()

        while stopwatch_obj.state is States.START:
            sleep(1.0)
            stopwatch_obj.elapsed_seconds += 1
            stopwatch_obj.seconds += 1
            struct_time_stopwatch = gmtime(float(stopwatch_obj.elapsed_seconds))
            stopwatch_formated_seconds = strftime(TIME_FORMAT, struct_time_stopwatch)

            time_window.nodelay(True)
            time_window.clear()
            time_window.addstr(stopwatch_formated_seconds[0:], curses.A_BOLD)
            time_window.refresh()
            try:
                stopwatch_character = time_window.getkey()
                if stopwatch_character == "p":
                    stopwatch_obj.pause()
                    info["stopwatch_state"] = States.PAUSE.value
                    info["elapsed_seconds"] = info["elapsed_seconds"] + stopwatch_obj.seconds
                    with open(INFO_FILE, 'w', encoding='utf-8') as info_file:
                        dump(info, info_file, indent=2)
                elif stopwatch_character == "s":
                    stopwatch_obj.stop()
                    info["stopwatch_state"] = States.STOP.value
                    info["elapsed_seconds"] = info["elapsed_seconds"] + stopwatch_obj.seconds
                    add_stopwatch_record(info["elapsed_seconds"] + stopwatch_obj.seconds)
                    with open(INFO_FILE, 'w', encoding='utf-8') as info_file:
                        dump(info, info_file, indent=2)
            except curses.error:
                stopwatch_character = None
    elif info["stopwatch_state"] == States.STOP.value: # Timer
        stdscr.clear()
        stdscr.addstr(3, 7, "Instructions:\n")
        stdscr.addstr(4, 5, "- Press p to pause the timer.\n")
        stdscr.refresh()

        if info["timer_state"] == States.WITHOUT_START.value:
            amount_of_seconds_for_the_timer: float = round(info["elapsed_seconds"] / 5)
            add_timer_record(amount_of_seconds_for_the_timer)
        else:
            amount_of_seconds_for_the_timer: float = info["leftover_break_time_in_seconds"]

        timer_obj.break_time_in_seconds = int(amount_of_seconds_for_the_timer)
        timer_obj.start()

        while timer_obj.state is States.START:
            sleep(1.0)
            if timer_obj.break_time_in_seconds > 0:
                timer_obj.break_time_in_seconds -= 1
            else:
                timer_obj.stop()
                info["timer_state"] = States.WITHOUT_START.value
                info["leftover_break_time_in_seconds"] = 0
                info["elapsed_seconds"] = 0
                info["stopwatch_state"] = States.WITHOUT_START.value
                PlaySound(BELL_SOUND_FILE, SND_FILENAME)

            struct_time_timer = gmtime(timer_obj.break_time_in_seconds)
            timer_formated_seconds = strftime(TIME_FORMAT, struct_time_timer)

            time_window.nodelay(True)
            time_window.clear()
            time_window.addstr(timer_formated_seconds[0:], curses.A_BOLD)
            time_window.refresh()
            try:
                timer_character = time_window.getkey()
                if timer_character == "p":
                    timer_obj.pause()
                    info["timer_state"] = States.PAUSE.value
                    info["leftover_break_time_in_seconds"] = timer_obj.break_time_in_seconds
                    with open(INFO_FILE, 'w', encoding='utf-8') as info_file:
                        dump(info, info_file, indent=2)
            except curses.error:
                timer_character = None

        with open(INFO_FILE, 'w', encoding='utf-8') as info_file:
            dump(info, info_file, indent=2)

fomodoro = wrapper(main)
