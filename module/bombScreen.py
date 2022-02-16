import time
from enum import Enum


from cv2 import cv2

from .config import Config
from .image import Image
from .logger import LoggerEnum, logger, logger_translated
from .mouse import *
from .utils import *
from .telegram import TelegramBot


class BombScreenEnum(Enum):
    NOT_FOUND = -1
    LOGIN = 0
    HOME = 1
    HEROES = 2
    TREASURE_HUNT = 3
    CHEST = 4
    POPUP_ERROR = 5
    SETTINGS = 6


class BombScreen:

    def wait_for_screen(
        bombScreenEnum, time_beteween: float = 0.5, timeout: float = 60
    ):
        def check_screen():
            screen = BombScreen.get_current_screen()
            if screen == bombScreenEnum:
                return True
            else:
                return None
        res = do_with_timeout(
            check_screen, time_beteween=time_beteween, timeout=timeout
        )
        
        if res is None:
            raise Exception(f'Timeout waiting for screen {BombScreenEnum(bombScreenEnum).name}.')
        
        return res
    
    def wait_for_leave_screen(
        bombScreenEnum, time_beteween: float = 0.5, timeout: float = 60
    ):
        def check_screen():
            screen = BombScreen.get_current_screen()
            if screen == bombScreenEnum:
                return None
            else:
                return True

        return do_with_timeout(
            check_screen, time_beteween=time_beteween, timeout=timeout
        )


    def get_current_screen(time_beteween: float = 0.5, timeout: float = 20):
        targets = {
            BombScreenEnum.HOME.value: Image.TARGETS["identify_home"],
            BombScreenEnum.HEROES.value: Image.TARGETS["identify_heroes"],
            BombScreenEnum.LOGIN.value: Image.TARGETS["identify_login"],
            BombScreenEnum.TREASURE_HUNT.value: Image.TARGETS["identify_treasure_hunt"],
            BombScreenEnum.CHEST.value: Image.TARGETS["identify_hunt_chest"],
            BombScreenEnum.POPUP_ERROR.value: Image.TARGETS["popup_erro"],
            BombScreenEnum.SETTINGS.value: Image.TARGETS["identify_settings"],
        }
        max_value = 0
        img = Image.screen()
        screen_name = -1

        for name, target_img in targets.items():
            result = cv2.matchTemplate(img, target_img, cv2.TM_CCOEFF_NORMED)
            max_value_local = result.max()
            if max_value_local > max_value:
                max_value = max_value_local
                screen_name = name

        return screen_name if max_value > Config.get("threshold", "default") else -1

    def go_to_home(manager):
        current_screen = BombScreen.get_current_screen()
        if current_screen == BombScreenEnum.HOME.value:
            return
        elif current_screen == BombScreenEnum.TREASURE_HUNT.value:
            click_when_target_appears("button_back")
        elif current_screen == BombScreenEnum.HEROES.value:
            click_when_target_appears("buttun_x_close")
        elif current_screen == BombScreenEnum.CHEST.value:
            click_when_target_appears("buttun_x_close")
            return BombScreen.go_to_home(manager)
        else:
            Login.do_login(manager)
            return

        BombScreen.wait_for_screen(BombScreenEnum.HOME.value)

    def go_to_heroes(manager):
        current_screen = BombScreen.get_current_screen()
        
        if current_screen == BombScreenEnum.HOME.value:
            click_when_target_appears("button_heroes")
            BombScreen.wait_for_screen(BombScreenEnum.HEROES.value)
            
        elif current_screen == BombScreenEnum.HEROES.value:
            return
        
        elif current_screen == BombScreenEnum.CHEST.value or current_screen == BombScreenEnum.SETTINGS.value:
            click_when_target_appears("buttun_x_close")
            BombScreen.wait_for_leave_screen(BombScreenEnum.CHEST.value)
            BombScreen.go_to_home(manager)
            return BombScreen.go_to_heroes(manager) 
        
        else:
            Login.do_login(manager)
            BombScreen.go_to_heroes(manager)

    def go_to_treasure_hunt(manager):
        if BombScreen.get_current_screen() == BombScreenEnum.TREASURE_HUNT.value:
            return
        else:
            BombScreen.go_to_home(manager)
            click_when_target_appears("identify_home")
            BombScreen.wait_for_screen(BombScreenEnum.TREASURE_HUNT.value)
            
    def go_to_chest(manager):
        if BombScreen.get_current_screen() == BombScreenEnum.CHEST.value:
            return
        else:
            BombScreen.go_to_treasure_hunt(manager)
            click_when_target_appears("button_hunt_chest")
            BombScreen.wait_for_screen(BombScreenEnum.CHEST.value)
            
    def do_print_chest(manager):
        logger_translated("print chest", LoggerEnum.ACTION)
        
        if BombScreen.get_current_screen() != BombScreenEnum.TREASURE_HUNT.value:
            BombScreen.go_to_treasure_hunt(manager)
        
        click_when_target_appears("button_hunt_chest")
        BombScreen.wait_for_screen(BombScreenEnum.CHEST.value)
        image = None      
        try:
            if Config.get("screen", "print_full_screen"):
                image = Image.print_full_screen("chest", "chest_screen_for_geometry")
            else:
                image = Image.print_partial_screen("chest", "chest_screen_for_geometry")
        
            TelegramBot.send_message_with_image(image, "Se liga no BCOIN desse baú, não deixe de contribuir com a evolução do bot :D")
        except Exception as e:
            logger(str(e))
            logger("😬 Ohh no! We couldn't send your farm report to Telegram.", color="yellow", force_log_file=True)
        
        BombScreen.go_to_treasure_hunt(manager)
        manager.set_refresh_timer("refresh_print_chest")
        


class Login:
    def do_login(manager):
        current_screen = BombScreen.get_current_screen()
        logged = False

        closeMetamaskWindow()

        if current_screen != BombScreenEnum.LOGIN.value and current_screen != BombScreenEnum.NOT_FOUND.value and current_screen != BombScreenEnum.POPUP_ERROR.value:
            logged = True

        if not logged:
            logger_translated("login", LoggerEnum.ACTION)

            login_attepmts = Config.PROPERTIES["screen"]["number_login_attempts"]
        
            for i in range(login_attepmts):
                
                if BombScreen.get_current_screen() != BombScreenEnum.LOGIN.value:
                    refresh_page()
                    BombScreen.wait_for_screen(BombScreenEnum.LOGIN.value)

                logger_translated("Login", LoggerEnum.PAGE_FOUND)

                logger_translated("wallet", LoggerEnum.BUTTON_CLICK)
                if not click_when_target_appears("button_connect_wallet"):
                    refresh_page()
                    continue

                maximizeMetamaskNotification()

                logger_translated("sigin wallet", LoggerEnum.BUTTON_CLICK)
                if not click_when_target_appears("button_connect_wallet_sign"):
                    refresh_page()
                    continue

                if (BombScreen.wait_for_screen(BombScreenEnum.HOME.value) != BombScreenEnum.HOME.value):
                    logger("🚫 Failed to login, restart proccess...")
                    continue
                else:
                    logger("🎉 Login successfully!")
                    logged = True
                    break

        manager.set_refresh_timer("refresh_login")
        return logged


class Hero:

    xtime = None
    hero_quantity_at_home = 0

    def who_needs_work(manager, xtime):

        Hero.xtime = xtime

        logger_translated(f"Heroes to work", LoggerEnum.ACTION)
        heroes_bar = [
            "hero_bar_0", "hero_bar_10", "hero_bar_20",
            "hero_bar_30", "hero_bar_40", "hero_bar_50",
            "hero_bar_60", "hero_bar_70", "hero_bar_80",
            "hero_bar_90", "hero_bar_100"
            ]
        heroes_rarity = [
            "hero_rarity_Common", "hero_rarity_Rare", "hero_rarity_SuperRare", "hero_rarity_Epic", "hero_rarity_Legend", "hero_rarity_SuperLegend"
        ]

        scale_factor = 10

        if xtime == 1:
            BombScreen.go_to_home(manager)
            BombScreen.go_to_heroes(manager)
            Hero.hero_quantity_at_home = 0
        if xtime == 2 or xtime == 3:
            BombScreen.go_to_heroes(manager)

        if xtime == 1:
            logger("Vai clicar no all amarelo")
            click_when_target_appears("all_yellow", timeout=2)
            logger("Vai clicar no all verde")
            click_when_target_appears("all_green", timeout=3)
            time.sleep(2)
            logger("Fim clique botoes")


        def click_available_heroes(page_number):

            hero_mod = 'heroes_home_' + str(xtime)

            while (True):
                screen_img = Image.screen()

                buttons_position = Image.get_target_positions("button_home_unchecked", screen_image=screen_img)

                logger("Pagina atual " + str(page_number))

                logger(f"👁️  Quantidade botoes Home habilitados - {len(buttons_position)}")

                if not buttons_position:
                    return Hero.hero_quantity_at_home

                if Hero.hero_quantity_at_home == Config.get('house', 'hero_quantity'):
                    logger("Casa cheia")
                    return Hero.hero_quantity_at_home

                x_buttons = buttons_position[0][0]
                height, width = Image.TARGETS["hero_search_area"].shape[:2]
                screen_img = screen_img[:,x_buttons-width:x_buttons, :]
                logger("↳", end=" ", datetime=False)

                need_print = False
                for index, button_position in enumerate(buttons_position):

                    if not need_print:
                        if page_number == 2:
                            if index >= len(buttons_position) - Hero.hero_quantity_at_home:
                                logger("CHEGOU NO FINAL ANTES DA CASA")
                                return Hero.hero_quantity_at_home

                        if Hero.hero_quantity_at_home == Config.get('house', 'hero_quantity'):
                            logger("Casa cheia")
                            return Hero.hero_quantity_at_home

                        x,y,w,h = button_position
                        search_img = screen_img[y:y+height, :, :]

                        rarity_max_values = [Image.get_compare_result(search_img, Image.TARGETS[rarity]).max() for rarity in heroes_rarity]
                        rarity_index, rarity_max_value= 0, 0
                        for i, value in enumerate(rarity_max_values):
                            rarity_index, rarity_max_value = (i, value) if value > rarity_max_value else (rarity_index, rarity_max_value)

                        hero_rarity = heroes_rarity[rarity_index].split("_")[-1]

                        life_max_values = [Image.get_compare_result(search_img, Image.TARGETS[bar]).max() for bar in heroes_bar]
                        life_index, life_max_value= 0, 0
                        for i, value in enumerate(life_max_values):
                            life_index, life_max_value = (i, value) if value >= life_max_value else (life_index, life_max_value)

                        if Config.get(hero_mod, hero_rarity) >= 0 and  life_index*scale_factor <= Config.get(hero_mod, hero_rarity):
                            click_randomly_in_position(x,y,w,h)

                            Hero.hero_quantity_at_home += 1
                            logger(f"💤; Adicionado - {hero_rarity}")
                            need_print = True
                            time.sleep(1)
                        else:
                            #logger(f"💪; Trabalhando - {hero_rarity}")
                            pass
                if not need_print:
                    break

            logger("", datetime=False)
            return Hero.hero_quantity_at_home

        scroll_and_click_on_targets(
            safe_scroll_target="hero_bar_vertical",
            repeat=Config.get('screen','scroll_heroes', 'repeat'),
            distance=Config.get('screen','scroll_heroes', 'distance'),
            duration=Config.get('screen','scroll_heroes', 'duration'),
            wait=Config.get('screen','scroll_heroes', 'wait'),
            function_between=click_available_heroes
        )

        manager.set_refresh_timer("refresh_heroes")

        if Hero.xtime == 1 or Hero.xtime == 2:
            logger(f"🏃 time {Hero.xtime} - {Hero.hero_quantity_at_home} new heros sent to explode everything 💣💣💣.")

            if Hero.hero_quantity_at_home == Config.get('house', 'hero_quantity'):
                Hero.refresh_hunt(manager)
            else:
                BombScreen.go_to_home(manager)
        else:
            logger(f"🏃 Second time - {Hero.hero_quantity_at_home} new heros sent to explode everything 💣💣💣.")
            Hero.refresh_hunt(manager)


        return Hero.hero_quantity_at_home

    def refresh_hunt(manager):
        logger_translated("hunting positions", LoggerEnum.TIMER_REFRESH)

        BombScreen.go_to_home(manager)
        BombScreen.go_to_treasure_hunt(manager)

        manager.set_refresh_timer("refresh_hunt")

        logger("End hunting positions")
        return True
    
    def do_check_error(manager):        
        current_screen = BombScreen.get_current_screen()
        
        if current_screen == BombScreenEnum.POPUP_ERROR.value or current_screen == BombScreenEnum.NOT_FOUND.value:
            logger_translated("Check screen error found, restarting...", LoggerEnum.ERROR)
            Login.do_login(manager)
            BombScreen.go_to_heroes(manager)
            BombScreen.go_to_treasure_hunt(manager)

        manager.set_refresh_timer("refresh_check_error")
