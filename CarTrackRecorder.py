import cv2 as cv

# RTMP 영상 스트림 (RTSP도 가능)
capture = cv.VideoCapture('rtmp://210.99.70.120/live/cctv007.stream')

# 추적 관련 변수
roi = None  # 자동차 추적 영역 (x, y, width, height)
tracking = False # 추적 여부 (자동차 선택 여부)
hist = None  # 색상 히스토그램
term_crit = (cv.TERM_CRITERIA_EPS | cv.TERM_CRITERIA_COUNT, 5, 1)  # MeanShift 조건

# 녹화 관련 변수
recording = False
video_writer = None
zoom_writer = None
cnt = 0

# 마우스 클릭 이벤트 함수
def select_car(event, x, y, flags, param):
    global roi, tracking, hist
    if event == cv.EVENT_LBUTTONDOWN:  # 왼쪽 버튼 클릭 시
        w, h = 70, 70  # 자동차 크기 설정
        roi = (x - w//2, y - h//2, w, h)
        tracking = True

        # ROI를 HSV로 변환 후 히스토그램 계산
        roi_frame = frame[roi[1]:roi[1]+roi[3], roi[0]:roi[0]+roi[2]]
        hsv_roi = cv.cvtColor(roi_frame, cv.COLOR_BGR2HSV)
        hist = cv.calcHist([hsv_roi], [0], None, [180], [0, 180])
        cv.normalize(hist, hist, 0, 255, cv.NORM_MINMAX)

# 창에 마우스 이벤트 등록
cv.namedWindow("Cheonan Station CCTV")
cv.setMouseCallback("Cheonan Station CCTV", select_car)

while True:
    ret, frame = capture.read()
    if not ret:
        break

    original_frame = frame.copy()
    
    # 자동차 추적
    if tracking and roi is not None:
        hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)
        back_proj = cv.calcBackProject([hsv], [0], hist, [0, 180], 1)
        
        _, roi = cv.meanShift(back_proj, roi, term_crit)  # MeanShift로 위치 업데이트

        x, y, w, h = roi
        cv.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)  # 추적 박스 표시
        cv.rectangle(original_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

        # 자동차 확대 영상
        car_zoomed = frame[y:y+h, x:x+w]
        car_zoomed = cv.resize(car_zoomed, (400, 400)) 
        cv.imshow("Tracking", car_zoomed)

        # 자동차 추적 영상도 녹화 (녹화 중일 때만)
        if recording and zoom_writer is not None:
            zoom_writer.write(car_zoomed)

    # 녹화 중일 때 빨간 원 표시
    if recording:
        cv.circle(frame, (50, 50), 10, (0, 0, 255), -1) 

    # 영상 녹화
    if recording and video_writer is not None:
        video_writer.write(original_frame)

    cv.imshow("Cheonan Station CCTV", frame)

    key = cv.waitKey(1) & 0xFF

    # 녹화 시작/종료
    if key == 32:  # Space 키
        if not recording:
            print("녹화 시작!")
            fourcc = cv.VideoWriter_fourcc(*'XVID')
            video_writer = cv.VideoWriter(f'recorded{cnt}.avi', fourcc, 20.0, (frame.shape[1], frame.shape[0]))
            zoom_writer = cv.VideoWriter(f'zoom_recorded{cnt}.avi', fourcc, 20.0, (400, 400))
            recording = True
        else:
            print("녹화 종료!")
            recording = False
            video_writer.release()
            zoom_writer.release()
            video_writer = None
            zoom_writer = None
            cnt += 1

    #  프로그램 종료
    if key == 27: #ESC 키
        break

capture.release()
cv.destroyAllWindows()