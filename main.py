import cv2 as cv
import numpy as np
import os
import sys

def show_image(title, img : list):
    img=cv.resize(img,(0,0),fx=0.25,fy=0.25)
    cv.imshow(title, img)
    cv.waitKey(0)
    cv.destroyAllWindows()

def extract_main_board(image, padding=15):
    # a patch of interest is cropped, in order to focus on the main board
    cropped_image = image[1150: 2900, 725: 2475, :]

    # image is converted to HSV color space
    hsv_image = cv.cvtColor(cropped_image, cv.COLOR_BGR2HSV)

    # mask parameters
    l = np.array([0, 177, 118])
    u = np.array([255, 255, 255])
    mask_table_hsv = cv.inRange(hsv_image, l, u)

    # mask is applied to the image
    main_board_hsv = cv.bitwise_and(
        cropped_image, cropped_image, mask=mask_table_hsv)

    # the result gets converted to gray
    gray_main_board = cv.cvtColor(main_board_hsv, cv.COLOR_BGR2GRAY)

    # apply Canny to find edges
    edges = cv.Canny(gray_main_board, 395, 578)

    # find the maximum and minimum values for the white pixels coordinates
    white_pixel_coordinates = np.where(edges == 255)
    min_x, min_y = np.min(white_pixel_coordinates[1]), np.min(
        white_pixel_coordinates[0])
    max_x, max_y = np.max(white_pixel_coordinates[1]), np.max(
        white_pixel_coordinates[0])

    # use the padding to find accuratey the dominoes
    # that go slightly over the edge
    """ padding should always divide by 15 """

    padding = 15

    # use the coordinates to locate the corners of the board

    top_left = (min_x - padding, min_y - padding)
    top_right = (min_x - padding, max_y + padding)
    bottom_left = (max_x + padding, min_y - padding)
    bottom_right = (max_x + padding, max_y + padding)

    # the desired dimesions of the extracted board image

    width = 2250 + 2 * padding
    height = 2250 + 2 * padding

    # matrix containing the actual positions of the pixels in the image
    board = np.array([top_left, top_right, bottom_left,
                     bottom_right], dtype="float32")

    # matrix containing the desired positions of the pixels in the final image
    centered_board = np.array([[0, 0], [0, width], [height, 0], [
                              height, width]], dtype="float32")

    # apply the transformation
    M = cv.getPerspectiveTransform(board, centered_board)
    result = cv.warpPerspective(cropped_image, M, (width, height))

    return result
    # show_image("result", result)

def mark_lines(padding: int = 15):
    lines_vertical = []
    lines_horizontal = []
    # image is (2250 + 2 * padding) x (2250 + 2 * padding) pixels
    # each square from the game board is equal to the others
    # we can equally split (2250 + padding) pixels into 225 squares
    # 15 on each row and column
    for i in range(0, 2251 + 2 * padding, 150 + padding // 15):
        l = []
        l.append((0, i))
        l.append((2249 + 2 * padding, i))
        lines_vertical.append(l)

    for i in range(0, 2251 + 2 * padding, 150 + padding // 15):
        l = []
        l.append((i, 0))
        l.append((i, 2249 + 2 * padding))
        lines_horizontal.append(l)

    return (lines_vertical, lines_horizontal)

def split_board(lines_horizontal: list, lines_vertical: list, padding=10):
    # this function returns the pixel coordinates of the corners
    # for each square on the board
    # that are further used in patch extraction

    cells = []
    for i in range(15):
        for j in range(15):
            x_min, y_min, x_max, y_max = [
                lines_horizontal[i][0][0],
                lines_vertical[j][0][1],
                lines_horizontal[i + 1][0][0],
                lines_vertical[j + 1][0][1]
            ]
            if 0 < i < 14 and 0 < j < 14:
                x_min -= padding
                x_max += padding
                y_min -= padding
                y_max += padding

            cells.append([(y_min, y_max), (x_min, x_max)])

    return cells

def map_positions_to_board(cells):
    squares_positions = {f"{y}{x}": [] for x in [
        chr(i) for i in range(65, 80)] for y in range(1, 16)}

    for key, cell in zip(squares_positions.keys(), cells):
        squares_positions[key] = cell

    return squares_positions

def get_patch(image, y_coords: tuple, x_coords: tuple):
    y_min, y_max = y_coords
    x_min, x_max = x_coords
    return image[y_min: y_max, x_min: x_max, :]

def detect_circles(src):

    gray = cv.cvtColor(src, cv.COLOR_BGR2GRAY)
    gray = cv.medianBlur(gray, 5)
    rows = gray.shape[0]

    # extract circles from the gray image
    circles = cv.HoughCircles(gray, cv.HOUGH_GRADIENT, 1, rows / 8,
                              param1=100, param2=30,
                              minRadius=10, maxRadius=22)

    valid_circles = []

    # filter false positives by keeping only black circles

    if circles is not None:
        circles = np.uint16(np.around(circles))
        for (x, y, r) in circles[0, :]:
            circle_patch = gray.astype(np.float64)[y - r:y + r, x - r:x + r]
            mean_pixel_value = np.mean(circle_patch)

            if mean_pixel_value < 80:
                valid_circles.append((x, y, r))

    return len(valid_circles)

def detect_empty_domino(image, y_coords: tuple, x_coords: tuple):
    y_min, y_max = y_coords
    x_min, x_max = x_coords

    # select an inner patch
    y_min += 30
    y_max -= 30
    x_min += 30
    x_max -= 30

    patch = image[y_min: y_max, x_min: x_max, :]
    # return the mean value of the pixels inside the patch
    return np.mean(patch)

def get_points_position():

    point_positions = {x: [] for x in range(1, 6)}
    point_positions[5] = ['1A', '1O', '15A', '15O']

    point_positions[4] = ['1D', '1L', '2F', '2J',
                          '4A', '4O', '6B', '6N',
                          '10B', '10N', '12A', '12O',
                          '14F', '14J', '15D', '15L']

    point_positions[3] = ['1H', '2M', '2C', '3N',
                          '3B', '4D', '4L', '8A',
                          '8O', '12D', '12L', '13B',
                          '13N', '14C', '14M', '15H']

    point_positions[2] = ['3E', '3K', '4F', '4J',
                          '5C', '5M', '6D', '6L',
                          '10D', '10L', '11C', '11M',
                          '12F', '12J', '13E', '13K']

    point_positions[1] = ['5E', '5G', '5I', '5K',
                          '6F', '6J', '7E', '7K',
                          '9E', '9K', '10F', '10J',
                          '11E', '11G', '11I', '11K']

    board_positions = {}

    for key in point_positions.keys():
        for value in point_positions[key]:
            board_positions[value] = key

    return board_positions

def get_sidetrack_positions():
    # the values for each position on the outside track 
    # are found inside ./positions.txt

    with open(f"./positions.txt", "r") as f:
        lines = f.readlines()
        lines = [line.split() for line in lines]
        values = [int(line[0]) for line in lines if line] 
        positions = {x : y for x,y in zip(range(102), values)}
        return positions
    
def calculate_score(point_positions: dict, dominoes : dict, player1_position : int , player2_position : int, turn : bool, side_path_dominoes : dict):
    # turn = 0 -> player1 turn
    # turn = 1 -> player2 turn
    new_player1_score = player1_position
    new_player2_score = player2_position

    # flags are used to give the +3 bonus only once per round
    flag_player1 = True
    flag_player2 = True
    # if a player places a domino on a special position
    score = 0
    for key in dominoes.keys():
        if key in point_positions.keys():
            # check if there is a double domino played i.e check if both values
            # are equal
            if len(set(dominoes.values())) == 1:
                score += 2 * point_positions[key]
            else:
                score +=  point_positions[key]
            
            # check whose turn it is
            if turn == 0:
                new_player1_score += score
            else:
                new_player2_score += score

        # the players can get the +3 bonus only once
        if dominoes[key] == side_path_dominoes[player1_position] and flag_player1:
            new_player1_score += 3
            flag_player1 = False
        
        if dominoes[key] == side_path_dominoes[player2_position] and flag_player2:
            new_player2_score += 3
            flag_player2 = False

        
    if turn == 0 :
        gained_score = new_player1_score - player1_position
    else:
        gained_score = new_player2_score - player2_position
        
    return (new_player1_score, new_player2_score, gained_score)
    
def get_player_turns(file):
    # this function looks inside {game_number}_mutari.txt
    # checks which player's turn is
    with open(file, "r") as f: 
        turns = []
        lines = f.readlines()

        for line in lines:
            if line == "\n": 
                continue
            if line[-2] == "1":
                turns.append(0)
            else:
                turns.append(1)
    return turns

if __name__ == "main":
    test_dir_path = sys.argv[1]
    output_dir_path = sys.arg[2]

    try:
        os.mkdir(output_dir_path)
    except OSError as e:
        print(f"Error creating directory: {e}")

    if os.path.exists(test_dir_path):
        files = os.listdir(test_dir_path)
        jpgs = sorted([x for x in files if x.lower().endswith(".jpg")])
        jpg_names = [x[:-4] for x in jpgs]

        # how many pixels outside the main board
        # you want to include in your working image
        board_padding = 15
        detected_board = {}

        player1_score = 0
        player2_score = 0
        turns = []
        game_counter = 0
        turn_counter = 0

        point_positions = get_points_position()
        side_track_positions = get_sidetrack_positions()

        for jpg, name in zip(jpgs, jpg_names):
            if name.endswith("01"):
                game_counter += 1
                turns = get_player_turns(
                    test_dir_path + f"{game_counter}moves.txt")
                turn_counter = 0
                detected_board = {}
                player1_score = 0
                player2_score = 0

            image_path = test_dir_path + jpg
            image = cv.imread(image_path)

            board = extract_main_board(image, board_padding)
            lines_vertical, lines_horizontal = mark_lines(board_padding)
            cells = split_board(lines_horizontal, lines_vertical)
            squares_positions = map_positions_to_board(cells)

            txt_output_name = name + ".txt"
            txt_output_path = output_dir_path + txt_output_name

            turn = turns[turn_counter]
            turn_counter += 1

            dominoes_found = {}

            with open(txt_output_path, "w") as f:
                for key in squares_positions.keys():
                    if key not in detected_board.keys():
                        cell = get_patch(
                            board, squares_positions[key][0], squares_positions[key][1])

                        circles_found = detect_circles(cell)
                        if circles_found != 0:
                            detected_board[key] = circles_found
                            dominoes_found[key] = circles_found
                            f.write(f"{key} {circles_found}\n")
                        else:
                            if detect_empty_domino(board, squares_positions[key][0], squares_positions[key][1]) > 190:
                                detected_board[key] = 0
                                dominoes_found[key] = 0
                                f.write(f"{key} 0\n")

                player1_score, player2_score, score = calculate_score(
                    point_positions, dominoes_found, player1_score, player2_score, turn, side_track_positions)
                f.write(f"{score}")
    else:
        print(f"The folder path '{test_dir_path}' does not exist!")