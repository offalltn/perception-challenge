from kivy.utils import platform
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.core.audio import SoundLoader
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image
from kivy.properties import ObjectProperty,OptionProperty
from kivy.lang import Builder
from kivy.clock import Clock #clock to schedule the game update
from kivy.storage.jsonstore import JsonStore
from os.path import join
import random
import os
from jnius import autoclass,cast
from time import sleep
from kivmob import KivMob, TestIds
from kivy.uix.label import Label
from urllib.request import urlopen




PythonActivity = autoclass('org.kivy.android.PythonActivity')
Intent = autoclass('android.content.Intent')
String = autoclass('java.lang.String')
Activity = autoclass('android.app.Activity')



#here we create a custom class called ImageButton. It's a image, however with
# some button properties. We use this class to use the on_press event
class ImageButton(ButtonBehavior, Image):
    pass

# This is the App screen, all game scenes(menu and the game) extends this object
class AppScreen(FloatLayout):
    # MainApp referece, so we can call some functions provided by this object
    app = ObjectProperty(None)



    def on_resume(self):
        self.ads.request_interstitial()

    def show_interstitial(self):
        self.ads.show_interstitial()




# This is our menu screen.
class MenuScreen(AppScreen,App):
    sound = SoundLoader.load('res/back.wav')
    sound.play()
    ads = KivMob("ca-app-pub-6117636140856499~4746090954")
    ads.add_test_device("4CDD16593360DCE6C8EB508F5D02FCF5")
    ads.new_banner("ca-app-pub-6117636140856499/2510981294",top_pos=False)
    ads.request_banner()
    ads.show_banner()
    ads.new_interstitial("ca-app-pub-6117636140856499/7380164596")
    ads.request_interstitial()

    def __init__(self, app): #init the object, receiving the MainApp instance
        super(MenuScreen, self).__init__()
        self.app = app # get the MainApp reference

    # switch to the GameScreen

    def new_game(self):
        self.app.open_screen('game')


    def sound_track(self):
        if MenuScreen.sound.state == 'stop':
            MenuScreen.sound.play()
        else:
            MenuScreen.sound.stop()


    def share(self):
        intent = Intent()
        intent.setAction(Intent.ACTION_SEND)
        intent.putExtra(Intent.EXTRA_TEXT, cast('java.lang.CharSequence', String('Wow, I just scored %d on Perception Challenge. Check this game: https://play.google.com/store/apps/details?id=omcj.apps.perceptionchallenge' % (self.best_score))))
        intent.setType('text/plain')
        chooser = Intent.createChooser(intent, String('Share...'))
        PythonActivity.mActivity.startActivity(chooser)


    # will be called when our screen be displayed
    def run(self):
        self.best_score = self.app.store.get('score')['best'] # get the best score saved



#Our game screen, where everything happens :)
class GameScreen(AppScreen):
    sound1 = SoundLoader.load('res/yay.wav')
    sound2 = SoundLoader.load('res/wrong.wav')
    sound3 = SoundLoader.load('res/over.wav')
    mylist2 =[]
    mylist = []
    restart_count = 0






    def __init__(self, app): #init the object, receiving the MainApp instance
        super(GameScreen, self).__init__()
        self.app = app
        self.init()

    #initialize defaults values to start a new game
    def init(self):
        self.best_level = self.app.store.get('score')['best'] # best level
        self.level = self.best_level # the current level
        self.game_grid = self.ids.game_grid # the game grid widget instance
        self.label_level = self.ids.label_level # the label widget to show the current level
        self.grid_size = 2 #we are using a grid layout to show our blocks, the fist level has a 2x2 grid
        self.last_id = None #last btn blinked
        self.first_id = None
        self.remain_interaction = 4 # number of blinks before turn off
        self.can_click = False # if the user can choose a block. Only true while not blinking
    # called when the game scene be displayed
    def run(self):
        self.start_game()

    # start a new game round
    def start_game(self, dt = None):
        self.can_click = False #while playing, user cannot choose a block
        self.ids.label_last_block.text = "" # clear the id of last blinked block
        self.check_best() #check if user has a new highscore
        self.ids.label_best.text = 'Best level: ' + str(self.best_level) # show the best score in the screen
        self.ids.restart.pos_hint = {'x': -1, 'y': 0.025} #hide the restart button
        self.ids.image_win.pos_hint = {'x': -1, 'y': 0.025} #hide the restart button
        self.ids.image_gameover.pos_hint = {'x': -1, 'y': 0.025} #hide the restart button
        self.ids.fivelevels.pos_hint = {'x': -1, 'y': 0.025} #hide the restart button
        self.ids.image_lose.pos_hint = {'x': -1, 'y': 0.025} #hide the restart button
        self.ids.nextlevel.pos_hint = {'x': -1, 'y': 0.025} #hide the restart button
        self.ids.nextlevelads.pos_hint = {'x': -1, 'y': 0.025} #hide the restart button
        self.ids.startover.pos_hint = {'x': -1, 'y': 0.025} #hide the restart button
        self.ids.full_lives.pos_hint = {'x' : 0.38 , 'y' : 0.68}
        self.ids.two_lives.pos_hint = {'x' : -1 , 'y' : 0.75}
        self.ids.one_live.pos_hint = {'x' : -1 , 'y' : 0.75}
        self.ids.no_lives.pos_hint = {'x' : -1 , 'y' : 0.75}

        Clock.unschedule(self.update) # stop updating the game screen
        self.label_level.text = 'Level: ' + str(self.level) #show the current level
        if self.level in range(50,101):
            self.remain_interaction = random.randint(10, self.level) #generate a random number of interactions
        else:
            self.remain_interaction = random.randint(1 + self.level, self.level*2) #generate a random number of interactions
        self.draw_screen() #show the blocks in the screen

        # here we set the speed of the animation
        if self.level in range(1,6):
            interval = 1 - self.level*0.1
        elif self.level in range(6,11):
            interval = 0.1 - self.level*0.001
        elif self.level in range(11,21):
            interval = 0.1 - self.level*0.002
        elif self.level in range(21,31):
            interval = 0.1 - self.level*0.003
        elif self.level in range(31,41):
            interval = 0.1 - self.level*0.004
        elif self.level in range(41,51):
            interval = 0.1 - self.level*0.005
        elif self.level in range(51,61):
            interval = 0.21 - self.level*0.002
        elif self.level in range(61,71):
            interval = 0.20 - self.level*0.002
        elif self.level in range(71,81):
            interval = 0.19 - self.level*0.002
        elif self.level in range(81,91):
            interval = 0.26 - self.level*0.002
        elif self.level in range(91,101):
            interval = 0.26 - self.level*0.002


        #update the screen using the interval calculated above
        Clock.schedule_interval(self.update, interval)

    #each update a different block will blink
    def update(self, dt):
        # when last_id is not none there is a green block in the screen
        if(self.last_id is not None):
            self.game_grid.ids.get(self.last_id).source = "res/block.png" #turn off the block
        if(self.first_id is not None):
            self.game_grid.ids.get(self.first_id).source = "res/block.png" #turn off the block



        if self.remain_interaction == 0: #if executed all interactions
            Clock.unschedule(self.update) #stop updating the screen
            self.ids.label_last_block.text = 'Click on the last block that blinked' #ask user to click in a block
            if self.level in range(81,101) and self.random_fisrt_or_last == self.first_id:
                self.ids.label_last_block.text = 'Click on the first block that blinked' #ask user to click in a block
            elif self.level in range(81,101) and self.random_fisrt_or_last == self.last_id:
                self.ids.label_last_block.text = 'Click on the last block that blinked' #ask user to click in a block
            elif self.level in range(51,81) :
                self.ids.label_last_block.text = 'Click on the first block that blinked' #ask user to click in a block
            elif self.level in range(1,51) :
                self.ids.label_last_block.text = 'Click on the last block that blinked' #ask user to click in a block

            self.can_click = True # allow the click
            return

        #if we can still blinking:

        id = 'btn_' + str(random.randint(0, self.grid_size*self.grid_size-1)) #generate a random int to blink a random block
        self.game_grid.ids.get(id).source=random.choice([x for x in os.listdir("res2/")]) #make this block border green
        self.last_id = id # save the id of the green block
        self.remain_interaction -= 1
        self.mylist.append(str(id))
        self.first_id = self.mylist[0]
        self.random_fisrt_or_last = random.choice([self.first_id,self.last_id])


    # draw the blocks in the screen
    def draw_screen(self):
        self.game_grid.clear_widgets() # this command remove all children(blocks) from the game_grid

        # according to the level, we can change the size of the grid
        if(self.level < 3):
            self.game_grid.cols = 2
            self.game_grid.rows = 2
            self.grid_size = 2
        elif self.level < 5:
            self.game_grid.cols = 3
            self.game_grid.rows = 3
            self.grid_size = 3
        elif self.level < 10:
            self.game_grid.cols = 4
            self.game_grid.rows = 4
            self.grid_size = 4
        elif self.level < 15:
            self.game_grid.cols = 5
            self.game_grid.rows = 5
            self.grid_size = 5
        elif self.level < 20:
            self.game_grid.cols = 6
            self.game_grid.rows = 6
            self.grid_size = 6
        elif self.level < 30:
            self.game_grid.cols = 7
            self.game_grid.rows = 7
            self.grid_size = 7
        elif self.level < 40:
            self.game_grid.cols = 8
            self.game_grid.rows = 8
            self.grid_size = 8
        elif self.level < 50:
            self.game_grid.cols = 9
            self.game_grid.rows = 9
            self.grid_size = 9
        elif self.level < 60:
            self.game_grid.cols = 3
            self.game_grid.rows = 3
            self.grid_size = 3
        elif self.level < 70:
            self.game_grid.cols = 4
            self.game_grid.rows = 4
            self.grid_size = 4
        elif self.level < 80:
            self.game_grid.cols = 5
            self.game_grid.rows = 5
            self.grid_size = 5
        elif self.level < 90:
            self.game_grid.cols = 6
            self.game_grid.rows = 6
            self.grid_size = 6
        elif self.level < 100:
            self.game_grid.cols = 7
            self.game_grid.rows = 7
            self.grid_size = 7


        # this is a block in KV lang.
        btn_str = '''
ImageButton:
    source: "res/block.png"
    allow_stretch: True
    keep_ratio: False'''


        # generate a grid_sizeXgrid_size grid
        for i in range(0, self.grid_size*self.grid_size):
            btn = Builder.load_string(btn_str) # create a ImageButton from the string
            id = 'btn_' + str(i)
            btn.id = id # set the button ID
            self.game_grid.ids[id] = btn #add this button to the list of children of the GameGrid
            btn.bind(on_press=self.on_btn_press) # bind the press event
            self.game_grid.add_widget(btn) # and show this button on the grid
            self.mylist2.append('btn_'+ str(i))


    # grid button event
    def on_btn_press(self, btn):
        if(self.can_click is True): # check if the user can click
            self.can_click = False
            if self.level in range(5,95,5):
                self.ids.nextlevel.pos_hint = {'x': -1, 'y': 0.025} #hide the restart button
                self.ids.nextlevelads.pos_hint = {'x': 0.1, 'y': 0.88} #the restart button is visible now

            if(btn.id == self.last_id) and self.level in range(1,50):
                self.game_grid.ids.get(self.last_id).source = 'res/block_blink.png' # blink the clicked button
                self.ids.label_last_block.text = 'Right!' # the user was right
                self.game_grid.clear_widgets() #remove the current screen
                GameScreen.sound1.play()
                self.ids.image_win.pos_hint = {'x': 0.0, 'y': 0.0} #the restart button is visible now
                self.ids.nextlevel.pos_hint = {'x': 0.1, 'y': 0.88} #the restart button is visible now


            elif(btn.id == self.first_id) and self.level in range(50,80): # if the clicked button was the last one to blink
                self.game_grid.ids.get(self.first_id).source = 'res/block_blink.png' # blink the clicked button
                self.ids.label_last_block.text = 'Right!' # the user was right
                self.game_grid.clear_widgets() #remove the current screen
                GameScreen.sound1.play()
                self.ids.image_win.pos_hint = {'x': 0.0, 'y': 0.0} #the restart button is visible now
                self.ids.nextlevel.pos_hint = {'x': 0.1, 'y': 0.88} #the restart button is visible now


            elif(btn.id == self.random_fisrt_or_last) and self.level in range(90,101):
                self.game_grid.ids.get(self.last_id).source = 'res/block_blink.png' # blink the clicked button
                self.game_grid.ids.get(self.first_id).source = 'res/block_blink.png' # blink the clicked button
                self.ids.label_last_block.text = 'Right!' # the user was right
                self.game_grid.clear_widgets() #remove the current screen
                GameScreen.sound1.play()
                self.ids.image_win.pos_hint = {'x': 0.0, 'y': 0.0} #the restart button is visible now
                self.ids.nextlevel.pos_hint = {'x': 0.1, 'y': 0.88} #the restart button is visible now


            else:
                self.ids.label_last_block.text = 'Wrong :(' #user was wrong
                self.game_grid.clear_widgets() #remove the current screen
                self.ids.image_lose.pos_hint = {'x': 0.0, 'y': 0.0} #the restart button is visible now
                GameScreen.sound2.play()
                self.ids.restart.pos_hint = {'x': 0.1, 'y': 0.88} #the restart button is visible now

    # compare the current level with the highscore
    def check_best(self):
        if self.level > self.best_level:
            self.best_level = self.level
            self.app.store.put('score', best=self.level) #save the best score. We are saving it in the key 'score', in the child 'best'



    # open the menu screen
    def go_menu(self):
        Clock.unschedule(self.update)
        self.init()
        self.app.open_screen('menu')


    # restart the first level
    def restart(self):
        self.mylist.clear()
        self.restart_count += 1
        Clock.unschedule(self.update)

        if self.restart_count == 3 :
            self.app.store.put('score', best= self.level - 5) #save the best score. We are saving it in the key 'score', in the child 'best'
            Clock.unschedule(self.update)
            self.init()
            self.game_grid.clear_widgets() #remove the current screen
            self.ids.image_lose.pos_hint = {'x': -1, 'y': 0.025} #hide the restart button
            self.ids.fivelevels.pos_hint = {'x': 0.0, 'y': 0.0} #the restart button is visible now
            GameScreen.sound2.stop()
            GameScreen.sound3.play()
            Clock.schedule_once(self.start_game, 4) #wait a second and start the next level
            #self.start_game()
            self.ids.full_lives.pos_hint = {'x' : -1 , 'y' : 0.75}
            self.ids.no_lives.pos_hint = {'x' : 0.38 , 'y' : 0.68}

        elif self.restart_count == 2:
            self.app.store.put('score', best= self.level) #save the best score. We are saving it in the key 'score', in the child 'best'
            #Clock.schedule_once(self.start_game, 1.5) #wait a second and start the next level
            Clock.unschedule(self.update)
            self.init()
            self.start_game()
            self.ids.full_lives.pos_hint = {'x' : -1 , 'y' : 0.75}
            self.ids.one_live.pos_hint = {'x' : 0.38 , 'y' : 0.68}


        elif self.restart_count == 1:
            self.app.store.put('score', best= self.level) #save the best score. We are saving it in the key 'score', in the child 'best'
            #Clock.schedule_once(self.start_game, 1.5) #wait a second and start the next level
            Clock.unschedule(self.update)
            self.init()
            self.start_game()
            self.ids.full_lives.pos_hint = {'x' : -1 , 'y' : 0.75}
            self.ids.two_lives.pos_hint = {'x' : 0.38 , 'y' : 0.68}


        else:
            self.restart_count = 0
            self.app.store.put('score', best= self.level) #save the best score. We are saving it in the key 'score', in the child 'best'
            #Clock.schedule_once(self.start_game, 1.5) #wait a second and start the next level
            Clock.unschedule(self.update)
            self.init()
            self.start_game()



    def nextlevel(self):
        self.mylist.clear()
        self.restart_count = 0
        if self.level == 100:
            self.game_grid.clear_widgets() #remove the current screen
            self.ids.image_win.pos_hint = {'x': -1, 'y': 0.025} #hide the restart button
            self.ids.image_gameover.pos_hint = {'x': 0.0, 'y': 0.0} #the restart button is visible now
            self.ids.nextlevel.pos_hint = {'x': -1, 'y': 0.025} #hide the restart button
            self.ids.nextlevelads.pos_hint = {'x': -1, 'y': 0.025} #hide the restart button
            self.ids.startover.pos_hint = {'x': 0.1, 'y': 0.88} #the restart button is visible now
            GameScreen.sound1.stop()
            GameScreen.sound3.play()
            #self.app.store.put('score', best= 1) #save the best score. We are saving it in the key 'score', in the child 'best'

        else:
            self.level += 1  #user can go to the next level
            Clock.schedule_once(self.start_game, 1.5) #wait a second and start the next level

    def nextlevelads(self):
        self.mylist.clear()
        self.restart_nextlevel_count += 1
        self.level += 1  #user can go to the next level
        Clock.schedule_once(self.start_game, 1.5) #wait a second and start the next level

    def startover(self):
        self.mylist.clear()
        self.app.store.put('score', best= 1) #save the best score. We are saving it in the key 'score', in the child 'best'
        Clock.unschedule(self.update)
        self.init()
        self.start_game()





# This is the main app
# This object create our application and manage all game screens
class MainApp(App):

    #create the application screens

    def initilize_global_vars(self):
        root_folder = self.user_data_dir

    def build(self):
        data_dir = getattr(self, 'user_data_dir') #get a writable path to save our score
        self.store = JsonStore(join(data_dir, 'score.json')) # create a JsonScore file in the available location
        if(not self.store.exists('score')): # if there is no file, we need to save the best score as 1
            self.store.put('score', best=1)
        self.screens = {} # list of app screens
        self.screens['menu'] = MenuScreen(self) #self the MainApp instance, so others objects can change the screen
        self.screens['game'] = GameScreen(self)
        self.root = FloatLayout()
        self.open_screen('menu')
        try:
            urlopen('http://google.com') #Python 3.x
            return self.connected()
        except:
            return self.disconnected()

        return self.root

    def connected(self):
        print("internet is there")

    def disconnected(self):
        print("fuck you")
        self.root.clear_widgets()
        check_connectivity = Label(text ="Please Connect To Internet,Reopen The Game")
        return check_connectivity

    # show a new screen.
    def open_screen(self, name):
        self.root.clear_widgets() #remove the current screen
        self.root.add_widget(self.screens[name]) # add a new one
        self.screens[name].run() # call the run method from the desired screen

if __name__ == '__main__':
    MainApp().run()
