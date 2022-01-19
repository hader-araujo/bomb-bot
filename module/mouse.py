from .image import Image
import pyautogui
import time
from .utils import randomize, randomize_int
from .logger import logger

def click_on_multiple_targets(target: str):
    """click in a list of target. Returns number of clicks"""
    targets_positions = Image.get_target_positions(target)
    targets_randomized = randomize_values(targets_positions)
    click_count = 0
    for (x, y, move_duration, time_between, click_duration) in targets_randomized:
        pyautogui.moveTo(x, y, duration=move_duration, tween=pyautogui.easeOutQuad)
        time.sleep(time_between)
        pyautogui.click(duration=click_duration)
        click_count += 1
    
    return click_count

def click_one_target(target: str):
    """click in a target. Returns number of clicks"""
    click_count = 0
    try:
        x_left, y_top, w, h = Image.get_one_target_position(target)
        x, y, move_duration, click_duration, time_between  = randomize_values(x_left, w, y_top, h)
        pyautogui.moveTo(x, y, duration=move_duration, tween=pyautogui.easeOutQuad)
        time.sleep(time_between)
        pyautogui.click(duration=click_duration)
        click_count += 1
    except Exception as e:
        logger(f"Error: {e}")
    
    return click_count

def click_when_target_appears(target: str, time_beteween: float = 0.5, timeout: float = 10):
    """ Click in a target when it appears.
        It will check for target every `time_beteween` seconds.
        After timeout seconds it will return 0 if no target was found.
        Returns 1 if target was found.
    """
    start_time = time.time()
    count = 1
    while True:
        if time.time() - start_time > timeout:
            return 0
        clicks = click_one_target(target)
        logger(f"Try: {count}; clicks: {clicks}")
        count +=1
        if clicks > 0:
            return 1
        time.sleep(time_beteween)


def randomize_values(x, w, y, h):
    x_rand = randomize_int(x, w, 0.20)
    y_rand = randomize_int(y, h, 0.20)
    move_duration = randomize(0.1, 0.5)
    click_duration = randomize(0.05, 0.2)
    time_between = randomize(0.05, 0.3)

    return x_rand, y_rand, move_duration, click_duration, time_between



