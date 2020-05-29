import kivy #importing kivy module
from kivy.app import App
from kivy.uix.label import Label #label
from kivy.uix.gridlayout import GridLayout #layout
from kivy.uix.textinput import TextInput #textinput
from kivy.uix.button import Button # to use button
from kivy.uix.screenmanager import ScreenManager, Screen #interfaces
import socket_client #importing client program to connect with server
from kivy.clock import Clock #scheduling tasks
from kivy.core.window import Window
from kivy.uix.scrollview import ScrollView
import sys


kivy.require("1.10.1")

#first interface where user enters the details
class ConnectPage(GridLayout): #inherits from gridlayout
    
    def __init__(self, **kwargs):  #function runs on initialization
        super().__init__(**kwargs) #kwargs-double star allows us to pass through keyword arguments

        self.cols = 2  #grid 

        with open("prev_details.txt","r") as f: #reads the previous login details ( IP,port,Username )
            d = f.read().split(",") #splits with , delimiter
            prev_ip = d[0]
            prev_port = d[1]
            prev_username = d[2]

        self.add_widget(Label(text='IP:')) 
        self.ip = TextInput(text=prev_ip, multiline=False)  # grabs prev IP details.
        self.add_widget(self.ip) 

        self.add_widget(Label(text='Port:'))
        self.port = TextInput(text=prev_port, multiline=False)  # grabs prev Port details.
        self.add_widget(self.port)

        self.add_widget(Label(text='Username:'))
        self.username = TextInput(text=prev_username, multiline=False)  # grabs prev Username details.
        self.add_widget(self.username)

        # adding join button to connect to the server.
        self.join = Button(text="Join")
        self.join.bind(on_press=self.join_button) #binding an function after pressing the function. 
        self.add_widget(Label())  
        self.add_widget(self.join)

    def join_button(self, instance): #defining join_button method
        port = self.port.text
        ip = self.ip.text
        username = self.username.text
        with open("prev_details.txt","w") as f: #writing details to the txt file
            f.write(f"{ip},{port},{username}")
  
        info = f"Joining {ip}:{port} as {username}"    #updating infopage with joining message
        chat_app.info_page.update_info(info)
        chat_app.screen_manager.current = 'Info'  #getting the screen to the forefront.
        Clock.schedule_once(self.connect, 1)   #seconds which the info page is visible.

    # Connecting to the server
    def connect(self, _): # _  as the argument to schedule the things

        # Getting information for socket_client to connect to the server. Required are : IP,port,username
        port = int(self.port.text)
        ip = self.ip.text
        username = self.username.text

        if not socket_client.connect(ip, port, username, show_error): #show_error: error method to show error message on Info page.
            return

        # Creating chat page and activating it when we are connected to the server.
        chat_app.create_chat_page()
        chat_app.screen_manager.current = 'Chat' 



# Kivy does not provide scrollable label, so we need to create one
class ScrollableLabel(ScrollView):

    def __init__(self, **kwargs): #kwargs-double star allows us to pass through keyword arguments
        super().__init__(**kwargs) #kwargs-double star allows us to pass through keyword arguments

        # Layout is going to have one collumn
        self.layout = GridLayout(cols=1, size_hint_y=None)
        self.add_widget(self.layout)

        
        self.chat_history = Label(size_hint_y=None, markup=True)
        self.scroll_to_point = Label()

        # We add them to our layout
        self.layout.add_widget(self.chat_history)
        self.layout.add_widget(self.scroll_to_point)

    # Methos called externally to add new message to the chat history
    def update_chat_history(self, message):

        # First add new line and message itself
        self.chat_history.text += '\n' + message

        
        self.layout.height = self.chat_history.texture_size[1] + 15
        self.chat_history.height = self.chat_history.texture_size[1]
        self.chat_history.text_size = (self.chat_history.width * 0.98, None)

        self.scroll_to(self.scroll_to_point)



class ChatPage(GridLayout): #chat-screen
    def __init__(self, **kwargs): #kwargs-double star allows us to pass through keyword arguments
        super().__init__(**kwargs) #kwargs-double star allows us to pass through keyword arguments

        # We are going to use 1 column and 2 rows
        self.cols = 1
        self.rows = 2

        self.history = ScrollableLabel(height=Window.size[1]*0.9, size_hint_y=None)
        self.add_widget(self.history)

        # In the second row, we want to have input fields and Send button
        self.new_message = TextInput(width=Window.size[0]*0.8, size_hint_x=None, multiline=False)
        self.send = Button(text="Send")
        self.send.bind(on_press=self.send_message)

        # To be able to add 2 widgets into a layout with just one collumn, we use additional layout,
        bottom_line = GridLayout(cols=2)
        bottom_line.add_widget(self.new_message)
        bottom_line.add_widget(self.send)
        self.add_widget(bottom_line)



        # keypresses
        Window.bind(on_key_down=self.on_key_down)

        Clock.schedule_once(self.focus_text_input, 1)

        # And now, as we have out layout ready and everything set, we can start listening for incimmong messages

        socket_client.start_listening(self.incoming_message, show_error)


    # Gets called on key press
    def on_key_down(self, instance, keyboard, keycode, text, modifiers):

        # But we want to take an action only when Enter key is being pressed, and send a message
        if keycode == 40:
            self.send_message(None)

    # Gets called when either Send button or Enter key is being pressed
    # (kivy passes button object here as well, but we don;t care about it)
    def send_message(self, _):

        # Get message text and clear message input field
        message = self.new_message.text
        self.new_message.text = ''

        # If there is any message - add it to chat history and send to the server
        if message:
            # Our messages - use red color for the name
            self.history.update_chat_history(f'[color=dd2020]{chat_app.connect_page.username.text}[/color] > {message}')
            socket_client.send(message)

        # As mentioned above, we have to shedule for refocusing to input field
        Clock.schedule_once(self.focus_text_input, 0.1)


    # Sets focus to text input field
    def focus_text_input(self, _):
        self.new_message.focus = True

    # Passed to sockets client, get's called on new message
    def incoming_message(self, username, message):
        # Update chat history with username and message, green color for username
        self.history.update_chat_history(f'[color=20dd20]{username}[/color] > {message}')


# Simple information/error page : to get the connection status. #after clicking join button.
class InfoPage(GridLayout):
    def __init__(self, **kwargs): #kwargs-double star allows us to pass through keyword arguments
        super().__init__(**kwargs) #kwargs-double star allows us to pass through keyword arguments

        self.cols = 1

        # adding centered text
        self.message = Label(halign="center", valign="middle", font_size=30)

        self.message.bind(width=self.update_text_width) #auto binding

        # Adding widget to the layout
        self.add_widget(self.message)

    #updating message text in widget
    def update_info(self, message):
        self.message.text = message

    # updating text width based on the message
    def update_text_width(self, *_): #ignoring arguments
        self.message.text_size = (self.message.width * 0.9, None)


class EpicApp(App): #first execution method
    def build(self):

       
        self.screen_manager = ScreenManager() #multiple screens and change between them


        self.connect_page = ConnectPage()
        screen = Screen(name='Connect')
        screen.add_widget(self.connect_page)
        self.screen_manager.add_widget(screen)

        # Info page
        self.info_page = InfoPage()
        screen = Screen(name='Info')
        screen.add_widget(self.info_page)
        self.screen_manager.add_widget(screen)

        return self.screen_manager

    # We cannot create chat screen with other screens, as it;s init method will start listening
    def create_chat_page(self):
        self.chat_page = ChatPage()
        screen = Screen(name='Chat')
        screen.add_widget(self.chat_page)
        self.screen_manager.add_widget(screen)


# Error callback function

def show_error(message):
    chat_app.info_page.update_info(message)
    chat_app.screen_manager.current = 'Info'
    Clock.schedule_once(sys.exit, 10)

if __name__ == "__main__":
    chat_app = EpicApp()
    chat_app.run()