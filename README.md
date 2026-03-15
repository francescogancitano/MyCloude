# MyCloude

## Description
MyCloude is a simple ssh web terminal, it is design to be minimalistic and simple <br> 
and to access to your pc/server from you local internet or via public internet 

## Main Features
- **System Pulse**: you can monitor in real time your hardware resourses such as cpu ram network traffic etc <br>
                    it will register system health based on how much you use your resourses, <br>
                    the system status are **OK, WARNING. and CRITICAL**
- **SSH Web Terminal**: Interactive web terminal that supports multitasking activities, programmed using the **xterm.js** library
- **Asynchronous Security**: Modern FastAPI Backend and asynchronous, with JWT Token authentification.
- **Containerized**: Simple architecture using docker to always suite your software and to avoid system conflicts

---

## How to install

1) Be sure to have installed docker, git and sshd in your system
2) Be sure your user is in the docker group or your image won't compose
   if you need more help consult <a href="https://docs.docker.com/manuals/">docker manuals</a>

3) Now you have to clone this repository
   ```bash
   git clone https://github.com/francescogancitano/MyCloude.git
   ```

4) rename your **.env.example** file to **.env**
   ```bash
   mv .env.example .env
   ```
5) **THIS IS A VERY IMPORTANT AND CRUCIAL STEP** you must edit your .env file
6) after completing all of the steps before you can now compose your Image
   ```bash
   docker compose up -d --build
   ```

---

## How to use

1) **Open your browser and connect to http://[yourip]:[yourchosenwebport]**
2) you can login as admin, with password admin <br>
   **THIS IS A TEMPORARY USER, DELETE IT AS SOON AS POSSIBLE FOR SECURITY REASONS**
3) **Click connect to enter in your host** <br>
   if you encounter any problems during composing or during connection via web or via ssh <br>
   be sure to have modified your .env file, or if you renamed it correctly <br>
   if it doesn't work eighter try composing it again or cloning back again this repository
