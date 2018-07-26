import sys
import errno
import os  
import urllib.request
from selenium import webdriver  
from selenium.webdriver.chrome.options import Options  
from selenium.common.exceptions import NoSuchElementException  
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from time import sleep
import selenium.webdriver.chrome.service as Service

#다음 로그인 정보
daum_id = "다음아이디"
daum_pw = "다음비밀번호"
grpid = "카페그리드아이디"
fldid = "카페아이디"

#전역변수
BBS_LIST = []
FIRSTBBSDEPTH = ''
LASTBBSDEPTH = ''
path = 'File Save Path'
domain = 'http://cafe.daum.net';

#chrome driver 의 경로를 지정한다.
#현재 py 파일과 같은 폴더에 위치
chrome_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'chromedriver.exe')

#selenium service 에 chrome driver를 등록한다.
service = Service.Service(chrome_path)
service.start()

#chrome 실행 옵션
chrome_options = Options()  

chrome_options.add_argument("--headless")  #Headless 옵션. 모두 완성한 뒤 백그라운드로 돌릴 경우에 
chrome_options.add_argument("--disable-gpu")  #headless 모드일 경우 gpu 끄기
chrome_options.add_argument('--ignore-certificate-errors')  #SSL 관련 오류 무시
chrome_options.add_argument('--ignore-ssl-errors')  #SSL 관련 오류 무시
chrome_options.binary_location = 'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe'  #chrome 프로그램 설치 경로

driver = webdriver.Remote(service.service_url, desired_capabilities=chrome_options.to_capabilities())   #chrome 실행한다.

#daum 로그인
def login():
    driver.get("https://logins.daum.net/accounts/loginform.do")
    driver.implicitly_wait(2) #페이지가 열리기 까지 최대2초 기다린다.

    my_id = driver.find_element_by_id("id")       #아이디를 입력할 input 위치
    my_pw = driver.find_element_by_id("inputPwd") #비밀번호를 입력할 input 위치
    login_button = driver.find_element_by_id("loginBtn") #로그인버튼

    if login_button.is_displayed(): #로그인 버튼이 보일 경우에
        my_id.clear()
        my_id.send_keys(daum_id)
        my_pw.clear()
        my_pw.send_keys(daum_pw)
        login_button.click()
        sleep(0.2)

def go_cafe_list(page):

    global FIRSTBBSDEPTH
    global LASTBBSDEPTH
    global BBS_LIST

    bbs_depth = '&firstbbsdepth=%s&lastbbsdepth=%s' % (FIRSTBBSDEPTH, LASTBBSDEPTH)
    if page == 1:
        bbs_depth = ''
   
    page = '&prev_page=1&page=%d' % page
    url = '%s%s%s' % ('http://cafe.daum.net/_c21_/bbs_list?grpid='+grpid+'&fldid='+fldid+'&listnum=50&sortType=', bbs_depth, page)

    print(url)

    driver.get(url)
    driver.implicitly_wait(2) #페이지가 열리기 까지 최대2초 기다린다.
    try:
        #frame 이동
        frame = driver.find_element_by_id("down")
        driver.switch_to_frame(frame)
        #frame 이동 완료
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        #페이징 필수값인 첫 게시물, 마지막 게시물을 찾아 전역변수에 저장
        for js in soup.select('script'):
            js_text = js.text
            for line in js_text.splitlines():
                if ' FIRSTBBSDEPTH' in line:
                    jt = line.split('"')
                    print('line 1 : ' + jt[1])
                    FIRSTBBSDEPTH = jt[1]
                elif ' LASTBBSDEPTH' in line:
                    jt = line.split('"')
                    print('line 1 : ' + jt[1])
                    LASTBBSDEPTH = jt[1]
    
        #각 게시물의 접근 URL 을 추출한다.
        list_td = soup.select('table.bbsList td.subject')
        for a in list_td:
            href = a.select('a')[0]['href']
            BBS_LIST.append(href) #전역변수 bbs_list 에 크롤링할 게시물 url 목록을 저장한다.
        return len(list_a) #마지막페이지인지 확인을 위한 리스트 사이즈 반환
    except NoSuchElementException:
        return 0    #예외가 발생할 경우 (예: 본문이 존재하지 않을경우 및 페이지가 없을 경우)


#게시물 내용 가져오기
def get_article(url):
    driver.get(url)
    driver.implicitly_wait(2) #페이지가 열리기 까지 최대2초 기다린다.

    #frame 이동
    frame = driver.find_element_by_id("down")
    driver.switch_to_frame(frame)
    #frame 이동 완료

    html = driver.page_source   #frame 의 html 을 string 으로 가져온다.
    title = ''
    contents_text = ''
    soup = BeautifulSoup(html, 'html.parser')   #BeautifulSoup 으로 파싱

    #게시물 제목
    for div in soup.select('div.subject'):
        title = div.select('span.b')[0].text

    #게시물 작성 일시
    for div in soup.select('div.article_writer'):
        date = div.select('span.ls0')[0].text
    
    try:    
        print('[%s:%s]' % (date, title))
    except:
        pass
    
    #게시물 내용 및 본문 첨부 이미지 url 추출
    for wrap in soup.select('div#wrap'):
        for xmp in wrap.select('table#protectTable'):
            for p in xmp.select('p'):
                if p.text.strip() != '':
                    contents_text = contents_text + p.text.strip() + '\n'
                        
                for img in p.select('img'):
                    src = img['src']
                    if img.has_attr('data-filename'):
                        name = img['data-filename']
                        img_down(src, name, date)
                    elif img.has_attr('class'):
                        css = img['class']
                        if 'txc-image' in css:
                            names = src.split('/')
                            name = names[len(names) - 1]
                            img_down(src, '%s.%s' % (name, 'jpg'), date)
                    

    data_id = soup.select('input[name="dataid"]')[0]['value']
    
    try:
        #게시물 내용을 일자별 생성된 폴더에 text 파일로 저장
        content_path = '%s/%s%s' % (get_path(date), data_id, 'contents.txt')
        content_file = open(content_path, 'w', encoding='utf-8', newline='')
        content_file.write('%s : %s \n' % ('title', title))
        content_file.write('%s : %s \n' % ('pub_date', date))
        content_file.write('%s : %s \n' % ('contents', contents_text))
        content_file.close()
    except:
        print("Unexpected error:", sys.exc_info()[0])
        raise
    try:
        print(contents_text)
        #정크파일 제거
        os.remove(str('%s/%s' % (get_path(date), 'contents.txt')))
    except:
        pass

#이미지 다운로드
def img_down(img_url, img_name, pub_date):
    print('[%s:%s]' % (pub_date, img_url))
    
    file_name = '%s/%s' % (get_path(pub_date), img_name)
    if os.path.exists(file_name)==False:
        #디도스 감지로 튕기는 것을 막기위한 딜레이
        sleep(1)
        urllib.request.urlretrieve(img_url, file_name)
    else:
        #이미 파일이 존재할 경우에는 이미 수집한 게시물이므로 프로그램 종료
        pass

#파일 저장 경로 생성        
def get_path(pub_date):
    global path
    d = pub_date.split('.')
    year = d[0]
    month = d[1]
    day = d[2]
    re_path = '%s%s/%s/%s' % (path, year, month, day)
    mkdir_p(re_path)
    return re_path

#폴더 없으면 만든다
def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise
try:
    #main start
    login() #로그인 실행

    #로그인 완료 후 10페이지까지 (500개의 게시물) 서치를 진행한다.
    for page in range(1, 10):
        size = go_cafe_list(page)
        if size < 50:
            break
        sleep(1)    #튕김 방지를 위한 1초 딜레이

    for url in BBS_LIST:
        url = domain + url
        print(url)
        get_article(url)
        sleep(1)    #튕김 방지를 위한 1초 딜레이
finally:
    driver.quit()

#main end



