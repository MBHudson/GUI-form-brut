
import config


from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

import traceback
import os
import sys
from datetime import datetime
import time
import threading
import random
import argparse
import re
import functools


workDir = os.path.abspath(os.curdir)

threads = []


browsers = []


def ParseArgs():
    """
    Function get and parse command line keys.
    """
    args = []
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("-t", "--target", type=str,
                            help="Target URL for Bruter. For example: '--target=http://mysite.com/admin/'")
        parser.add_argument("-b", "--browser", type=str,
                            help="Browser for Bruter (*firefox, *ie, *chrome). *firefox by default.")
        parser.add_argument("-r", "--random", type=str,
                            help="If this key is True then Bruter uses random user and password in every iteration.")
        parser.add_argument("-T", "--threads", type=int, help="Thread's number.")
        parser.add_argument("-w", "--wait", type=int, help="Waiting for operation's finish (sec.).")
        parser.add_argument("-p", "--period", type=int,
                            help="Rump up period shows time (sec.) in which all test suite threads will start.")
        parser.add_argument("-L", "--logins", type=str, help="Path to user's list. Default: dict/users.txt")
        parser.add_argument("-P", "--passwords", type=str, help="Path to password's list. Default: dict/pwd.txt")
        parser.add_argument("-R", "--results", type=str, help="Path to result file. Default: result.txt")
        parser.add_argument("-g", "--generator", type=str,
                            help="Generate a lot of random strings for Bruter. Example: '-g [100,8,1,1,1,0,0,0]'.\n" +
                                 "This means:\n" +
                                 "1 number - number of strings, 2 - string's length, 3 - use or not Numbers," +
                                 "4 - use or not Latin Upper Case Chars, 5 - use or not Latin Lower Case Chars" +
                                 "6 - use or not Russian Upper case chars, 7 - use or not Russian Lower Case Chars,"
                                 "8 - use or not Special Simbols. Output file: dict/rnd_<date_time>.txt")
        args = parser.parse_args()
        if args.target != None:
            config.target = args.target
        if (args.browser == '*chrome') or (args.browser == '*ie'):
            config.selBrowserString = args.browser
        else:
            config.selBrowserString = '*firefox'
        if args.random != None:
            if args.random == 'True':
                config.randomCredentials = True
            else:
                config.randomCredentials = False
        if args.threads != None:
            config.brutThreads = args.threads
        if args.wait != None:
            config.timeout = args.wait
        if args.period != None:
            config.rumpUpPeriod = args.period
        if args.logins != None:
            if os.path.exists(args.logins):
                config.usersFile = args.logins
            else:
                config.usersFile = 'dict/users.txt'
        if args.passwords != None:
            if os.path.exists(args.passwords):
                config.passwordsFile = args.passwords
            else:
                config.passwordsFile = 'dict/pwd.txt'
        if args.results != None:
            if os.path.exists(args.results):
                config.resultFile = args.results
            else:
                config.resultFile = 'result.txt'
        if args.generator != None:
            params = []
            try:
                params = StringOfNumToNumsList(args.generator)
            except:
                pass
            finally:
                if len(params) >= 8:
                    config.randomGeneratorParameter = params
                else:
                    print('%s - Generator using default parameters from config file: %s' %
                          (datetime.now().strftime('%H:%M:%S %d.%m.%Y'), config.randomGeneratorParameter))
        print('%s - Parsing command line arguments, status: oK' % datetime.now().strftime('%H:%M:%S %d.%m.%Y'))
    except BaseException:
        print('%s - Parsing command line arguments, status: error' % datetime.now().strftime('%H:%M:%S %d.%m.%Y'))
        traceback.print_exc()
    finally:
        return args


def EstimateTime(numLogins=0, numPasswords=0, waitInSec=1, timeForStartingTreads=0):
    """
    Function returns info about estimate time.
    """
    try:
        es = numLogins * numPasswords * waitInSec + timeForStartingTreads
        eh = round(es / 3600)
        info = 'Users: %d, Passwords: %d, Full Estimated Time: %d sec. (~%d hours).' %\
               (numLogins, numPasswords, es, eh)
    except BaseException:
        traceback.print_exc()
        return 'Can\'t compute estimate time!'
    return info


def DurationOperation(func):
    """
    This is decorator for compute duration operation of functions. It works only with functions returning number >= 0.
    """

    def wrapper(*args, **kwargs):
        startTime = datetime.now()
        print('%s - Thread #%d, %s, starting ...' % (startTime.strftime('%H:%M:%S %d.%m.%Y'), args[0], str(func)))
        status = func(*args, **kwargs)
        stopTime = datetime.now()
        if status == 0:
            print('%s - Thread #%d, %s, status: oK' % (stopTime.strftime('%H:%M:%S %d.%m.%Y'), args[0], str(func)))
        else:
            print('%s - Thread #%d, %s, status: error' % (stopTime.strftime('%H:%M:%S %d.%m.%Y'), args[0], str(func)))
        duration = stopTime - startTime
        print('%s - Thread #%d, %s, duration operation: %s' %
              (stopTime.strftime('%H:%M:%S %d.%m.%Y'), args[0], str(func), str(duration)))
        return status

    return wrapper


def StringOfNumToNumsList(string):
    """
    Get some string with numbers and other simbols, for example:'[572,573,604,650]' or similar
    and convert it to list of numbers as [572, 573, 604, 650].
    """
    numList = []
    try:
        while len(string) != 0:
            s = ''
            i = 0
            flag = True
            while flag and i < len(string):
                if string[i] in '0123456789':
                    s = s + string[i]
                    i += 1
                else:
                    flag = False
            if s != '':
                numList.append(int(s))
            string = string[i + 1:]
    except:
        print('%s - Can\'t parse your string of numbers to list of numbers!' %
              datetime.now().strftime('%H:%M:%S %d.%m.%Y'))
        traceback.print_exc()
        return []
    return numList


def GetListFromFile(file):
    """
    This function get strings from file and put into list. Text-file must have #13#10
    """
    listFromFile = []
    if os.path.exists(file):
        try:
            with open(file) as fh:
                allStrings = fh.read()
                listFromFile = allStrings.split('\n')
        except BaseException:
            print('%s - Can\'t get list from file: %s' % (datetime.now().strftime('%H:%M:%S %d.%m.%Y'), file))
            traceback.print_exc()
            return []
    return listFromFile


def SeparateListByPieces(fullList, piecesNum):
    """
    Function get full list of objects and then divided into a number of parts. Last part may be bigger, than other.
    Function return a list of part of full list.
    """
    separate = []
    listLen = len(fullList)
    if (listLen > 0) and (piecesNum > 1):
        try:
            objectsInPieces = listLen // piecesNum
            for i in range(piecesNum):
                piece = [fullList[i * objectsInPieces + k] for k in range(objectsInPieces)]
                separate.append(piece)
            separate[piecesNum - 1] += fullList[piecesNum * objectsInPieces:]
        except BaseException:
            print('%s - Can\'t separate list of objects!' % datetime.now().strftime('%H:%M:%S %d.%m.%Y'))
            traceback.print_exc()
            return [fullList]
    else:
        separate = [fullList]
    return separate


@DurationOperation
def Reporting(instance=0, file='result.txt', creds=None, users=None, passwords=None, actualTime=0):
    """
    This function print results to file.
    """
    try:
        if os.path.exists(file):
            fileTo = open(file, 'a')
        else:
            fileTo = open(file, 'w')
        fileTo.write('\n%s - Thread #%d, Bruter finished check for\n' %
                     (datetime.now().strftime('%H:%M:%S %d.%m.%Y'), instance) +
                     'users = [\'%s\', ..., \'%s\'], %d items,\n' % (users[0], users[-1], len(users)) +
                     'passwords = [\'%s\', ..., \'%s\'], %d items.\n' % (passwords[0], passwords[-1], len(passwords)) +
                     'Actual time worked: %s\n' % str(actualTime))
        if (creds != None) and (creds != {}):
            fileTo.write('Suitable credentials: %s\n' % str(creds))
        else:
            fileTo.write('Bruter can\'t find suitable credentials.\n')
        print('%s - Thread #%d, Updating report file: \'%s\'' %
              (datetime.now().strftime('%H:%M:%S %d.%m.%Y'), instance, file))
        fileTo.close()
    except BaseException:
        traceback.print_exc()
        return 1
    return 0


@DurationOperation
def OpenBrowser(instance=0, opTimeout=10, browserString='*firefox', ffProfile=None):
    """
    Commands for opening new instance of WebDriver browser.
    """
    try:
        # Get new browser instance and put it into browser array. One browser for one thread.
        if browserString == '*chrome':
            chromeOptions = webdriver.ChromeOptions()
            chromeOptions.add_argument('--start-maximized')
            chromeOptions.add_argument('--log-path=' + workDir + '/browser_drivers/chromedriver.log')
            os.chdir(workDir + '/browser_drivers')
            browsers.append(webdriver.Chrome(executable_path=workDir + '/browser_drivers/chromedriver.exe',
                                             chrome_options=chromeOptions))
            os.chdir(workDir)
        elif browserString == '*ie':
            browsers.append(webdriver.Ie(executable_path=workDir + '/browser_drivers/IEDriverServer.exe',
                                         log_file=workDir + '/browser_drivers/iedriver.log'))
            browsers[len(browsers) - 1].maximize_window()
        else:
            ffp = webdriver.FirefoxProfile(ffProfile)
            browsers.append(webdriver.Firefox(firefox_profile=ffp, timeout=opTimeout))
            browsers[len(browsers) - 1].maximize_window()
    except BaseException:
        traceback.print_exc()
        return 1
    return 0


@DurationOperation
def GoingToTarget(instance=0, opTimeout=10, targetURL='', loginField="//input[@name='login']",
                  passwordField="//input[@name='password']", acceptButton="//input[@type='submit']"):
    """
    This funcion going to target's URL with form-based auth.
    """
    try:
        page = browsers[instance]
        page.get(targetURL)
        WebDriverWait(page, opTimeout).until(
            lambda el: el.find_element_by_xpath(loginField).is_displayed() and
                       el.find_element_by_xpath(passwordField).is_displayed() and
                       el.find_element_by_xpath(acceptButton).is_displayed(), 'Timeout while opening auth page.')
    except BaseException:
        traceback.print_exc()
        return 1
    return 0


@DurationOperation
def CloseBrowser(instance=0):
    """
    Try to close WebDriver browser.
    """
    if len(browsers) > 0:
        if browsers[instance] != None:
            try:
                browsers[instance].close()
                browsers[instance] = None
            except BaseException:
                traceback.print_exc()
                return 1
    return 0


def Cleaner():
    """
    Finalization step for Bruter.
    """
    status = 0
    try:
        # Stopping compute threads and closing browsers.
        for t in threads:
            if t != None:
                t._stop()
                t = None
        for b in range(len(browsers)):
            status += CloseBrowser(b)
        if status == 0:
            print('%s - Bruter finalize, status: oK' % datetime.now().strftime('%H:%M:%S %d.%m.%Y'))
    except BaseException:
        print('%s - Bruter finalize, status: error' % datetime.now().strftime('%H:%M:%S %d.%m.%Y'))
        traceback.print_exc()
        return 1
    return status


def GenerateRandomString(length=8, useNum=True, useEngUp=True, useEngLo=True, useRuUp=False, useRuLo=False,
                         useSpecial=False):
    """
    Function return random text-string definite length, that will be use as login or password.
    1 number - number of strings, 2 - string's length, 3 - use or not Numbers,
    4 - use or not English Upper Case Chars, 5 - use or not English Lower Case Chars,
    6 - use or not Russian Upper case chars, 7 - use or not Russian Lower Case Chars, 8 - use or not Special Simbols.
    """
    # There are possible simbols in alphabet.
    alphabet = {
        'dicNum': '1234567890',
        'dicEngCharUpperCase': 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
        'dicEngCharLowerCase': 'abcdefghijklmnopqrstuvwxyz',
        'dicRuCharUpperCase': 'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЬЫЪЭЮЯ',
        'dicRuCharLowerCase': 'абвгдеёжзийклмнопрстуфхцчшщьыъэюя',
        'dicSpecial': '!@#$%^&*()-_+=.,<>[]{}\|/`~"\':;'}

    # Preparing user's alphabet.
    usersAlphabet = ''
    if useNum:
        usersAlphabet += alphabet['dicNum']
    if useEngUp:
        usersAlphabet += alphabet['dicEngCharUpperCase']
    if useEngLo:
        usersAlphabet += alphabet['dicEngCharLowerCase']
    if useRuUp:
        usersAlphabet += alphabet['dicRuCharUpperCase']
    if useRuLo:
        usersAlphabet += alphabet['dicRuCharLowerCase']
    if useSpecial:
        usersAlphabet += alphabet['dicSpecial']
    usersAlpLen = len(usersAlphabet)

    textString = ''
    try:
        if (length > 0) and (usersAlphabet != ''):
            for i in range(length):
                textString += usersAlphabet[random.randint(0, usersAlpLen - 1)]
    except BaseException:
        textString = ''
        print('%s - Can\'t generate random string!' % datetime.now().strftime('%H:%M:%S %d.%m.%Y'))
        traceback.print_exc()
    finally:
        return textString


def GenerateListOfRandomStrings(numbers=10, length=8, useNum=True, useEngUp=True, useEngLo=True,
                                useRuUp=False, useRuLo=False, useSpecial=False):
    """
    Function return list of random text-string definite length, that will be use as login or password.
    1 number - number of strings, 2 - string's length, 3 - use or not Numbers,
    4 - use or not English Upper Case Chars, 5 - use or not English Lower Case Chars,
    6 - use or not Russian Upper case chars, 7 - use or not Russian Lower Case Chars, 8 - use or not Special Simbols.
    """
    rndList = []
    try:
        if numbers > 0:
            for i in range(numbers):
                rndList.append(GenerateRandomString(length, useNum, useEngUp, useEngLo, useRuUp, useRuLo, useSpecial))
    except BaseException:
        rndList = []
        print('%s - Can\'t generate list of random string!' % datetime.now().strftime('%H:%M:%S %d.%m.%Y'))
        traceback.print_exc()
    finally:
        return rndList


def GenerateFileWithRandomStrings(par=None):
    """
    Function create file with random text-string, that will be use as login or password.
    Example: Par = [100, 5, 1, 1, 1, 0, 0, 0]
    1 number - number of strings, 2 - string's length, 3 - use or not Numbers,
    4 - use or not English Upper Case Chars, 5 - use or not English Lower Case Chars,
    6 - use or not Russian Upper case chars, 7 - use or not Russian Lower Case Chars, 8 - use or not Special Simbols.
    """
    file = 'dict/rnd_' + datetime.now().strftime('%d_%m_%Y_%H_%M_%S') + '.txt'
    try:
        if not (os.path.exists('dict')):
            os.mkdir('dict')
        fileTo = open(file, 'a')
        if len(par) >= 8:
            for i in range(2, 8):
                if par[i] == 1:
                    par[i] = True
                else:
                    par[i] = False
            rndList = GenerateListOfRandomStrings(par[0], par[1], par[2], par[3], par[4], par[5], par[6], par[7])
        else:
            rndList = GenerateListOfRandomStrings(numbers=10, length=8, useNum=True, useEngUp=True, useEngLo=True,
                                                  useRuUp=False, useRuLo=False, useSpecial=False)
        if len(rndList) > 0:
            for string in rndList:
                fileTo.write(string + '\n')
        print('%s - Generate file with random strings: %s' % (datetime.now().strftime('%H:%M:%S %d.%m.%Y'), file))
        fileTo.close()
    except BaseException:
        print('%s - Can\'t generate file with random strings!' % datetime.now().strftime('%H:%M:%S %d.%m.%Y'))
        traceback.print_exc()
        return 1
    return 0


@DurationOperation
def Bruter(instance=0, opTimeout=3, loginField="", passwordField="", acceptButton="", successAuth="", failAuth="",
           users=None, passwords=None, randomization=False, result='result.txt'):
    """
    This function loops through user IDs and passwords and finds suitable credentials.
    """

    suitableCredentials = {}
    startTime = datetime.now()
    try:
        page = browsers[instance]
        modUsers = users[:]
        modPasswords = passwords[:]
        if randomization:
            print('%s - Thread #%d, shuffling users and passwords ...' %
                  (datetime.now().strftime('%H:%M:%S %d.%m.%Y'), instance))
            random.shuffle(modUsers)
            random.shuffle(modPasswords)
        print('%s - Thread #%d, trying to use credentials ...' %
              (datetime.now().strftime('%H:%M:%S %d.%m.%Y'), instance))
        for user in modUsers:
            for pwd in modPasswords:
                try:
                    page.find_element_by_xpath(loginField).clear()
                    page.find_element_by_xpath(loginField).send_keys(user)
                    page.find_element_by_xpath(passwordField).clear()
                    page.find_element_by_xpath(passwordField).send_keys(pwd)
                    page.find_element_by_xpath(acceptButton).click()
                    WebDriverWait(page, opTimeout).until(
                        lambda el: el.find_element_by_xpath(successAuth).is_displayed(), '')
                    suitableCredentials = {user: pwd}
                    print('%s - Thread #%d, found valid credentials: %s' %
                          (datetime.now().strftime('%H:%M:%S %d.%m.%Y'), instance, str({user: pwd})))
                    break
                except:
                    try:
                        WebDriverWait(page, opTimeout).until(
                            lambda el: el.find_element_by_xpath(failAuth).is_displayed(),
                            '%s - Thread #%d, Can\'t find auth fields! Possible connection problem.' %
                            (datetime.now().strftime('%H:%M:%S %d.%m.%Y'), instance))
                    except:
                        pass
            if suitableCredentials != {}:
                break
        threads[instance] = None
        Reporting(instance, result, suitableCredentials, users, passwords, datetime.now() - startTime)
    except:
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    pass
