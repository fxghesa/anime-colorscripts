""" A script that makes unicode art out of images. Used to make unicode art of
chara sprites for printing out to the terminal

Author: Phoney Badger (https://gitlab.com/phoneybadger)
(c) 08-08-2021
Modified: Juan Louis R (https://github.com/mizuday)
(c) 02-12-2021


Usage:
-run the shell script that downloads all the chara images
-adjust the paths in the main function of this script
-run the script. It should output the correct color files
"""
import re
import os
import numpy as np

try:
    import skimage.io as io
    import skimage.transform as tm
except ImportError:
    io = None
    tm = None

path_to_charalist = 'charalist.txt' 
path_to_images = 'images/original' 
output_path = 'colorscripts'         


def main():
    dest_small = os.path.join(output_path, 'small')
    dest_medium = os.path.join(output_path, 'medium')
    dest_large = os.path.join(output_path, 'large')
    os.makedirs(dest_small, exist_ok=True)
    os.makedirs(dest_medium, exist_ok=True)
    os.makedirs(dest_large, exist_ok=True)

    if os.path.exists(path_to_images) and any(f.endswith('.png') for f in os.listdir(path_to_images)):
        for file in os.listdir(path_to_images):
            chara = os.fsdecode(file)
            print(chara)
            if chara.endswith(".png"):
                chara = chara[:-4]
                try:
                    small_art, medium_art, large_art = get_chara_art(chara, path_to_images, with_resize=True)
                except Exception as e:
                    print(f"couldn't generate art for {chara}: {e}")
                    continue
                write_chara_to_file(chara, small_art, medium_art, large_art, output_path)
    elif os.path.exists(dest_large) and any(f.endswith('.txt') for f in os.listdir(dest_large)):
        # Convert existing large files to medium and small
        print("Converting existing large colorscripts to medium and small...")
        for file in os.listdir(dest_large):
            if file.endswith('.txt'):
                chara = file[:-4]
                with open(os.path.join(dest_large, file), 'r') as fp:
                    large_content = fp.read()
                grid = parse_full_block_art(large_content)
                medium_art = grid_to_half_blocks(grid)
                small_grid = downscale_nearest(grid, 16)
                small_art = grid_to_half_blocks(small_grid)

                with open(os.path.join(dest_medium, file), 'w') as fp:
                    fp.write(medium_art)
                with open(os.path.join(dest_small, file), 'w') as fp:
                    fp.write(small_art)
                with open(os.path.join(output_path, file), 'w') as fp:
                    fp.write(small_art)

    update_charalist()


def write_chara_to_file(chara, small_art, medium_art, large_art, out_dir):
    dest_small = os.path.join(out_dir, 'small')
    dest_medium = os.path.join(out_dir, 'medium')
    dest_large = os.path.join(out_dir, 'large')
    os.makedirs(dest_small, exist_ok=True)
    os.makedirs(dest_medium, exist_ok=True)
    os.makedirs(dest_large, exist_ok=True)

    with open(os.path.join(dest_small, f'{chara}.txt'), 'w') as f:
        f.write(small_art)
    with open(os.path.join(dest_medium, f'{chara}.txt'), 'w') as f:
        f.write(medium_art)
    with open(os.path.join(dest_large, f'{chara}.txt'), 'w') as f:
        f.write(large_art)
    with open(os.path.join(out_dir, f'{chara}.txt'), 'w') as f:
        f.write(small_art)


def get_chara_art(chara, path_images, with_resize=True):
    """Takes the name of a chara and generates small (8 lines), medium (16 lines), and large unicode art."""
    path = f'{path_images}/{chara}.png'
    original_image = io.imread(path)
    image_cropped = crop_image_to_content(original_image)

    if with_resize:
        height, width, channels = image_cropped.shape
        height_threshold = 32
        if height > height_threshold:
            print(f'{chara} too large')
            scale = height / 32
            image_cropped = tm.resize(image_cropped, (int(height / scale), int(width / scale), channels), anti_aliasing=False)
            image_cropped = image_cropped * 255

    medium_art = render_half_block(image_cropped)
    large_art = render_large_full_block(image_cropped)

    # Small: downscaled to 16px
    h, w, c = image_cropped.shape
    if h > 16:
        scale = h / 16
        small_cropped = tm.resize(image_cropped, (16, int(w / scale), c), anti_aliasing=False) * 255
    else:
        small_cropped = image_cropped
    small_art = render_half_block(small_cropped)

    return small_art, medium_art, large_art


def render_large_full_block(image_cropped):
    """Renders full-block art where each pixel is doubled horizontally."""
    image = np.repeat(image_cropped, 2, 1).astype(np.uint8)
    rows, columns, _ = image.shape

    string_matrix = np.full((rows, columns), fill_value=' ', dtype=str)
    string_matrix[image[:, :, 3] >= 128] = '█'

    art = ''
    for i in range(rows):
        art += '\n'
        old_color = None
        for j in range(columns):
            r, g, b = image[i, j, :3]
            new_color = get_color_escape(r, g, b, background=False)
            if new_color == old_color:
                color_escape = ''
            else:
                color_escape = new_color
                old_color = new_color

            art += f'{color_escape}{string_matrix[i, j]}'
    art += '\033[0m\n'
    return art


def render_half_block(image_cropped):
    """Renders compact half-block art using upper/lower half block glyphs."""
    image = image_cropped.astype(np.uint8)
    rows, columns, _ = image.shape

    grid = []
    for r in range(rows):
        row = []
        for c in range(columns):
            pixel = image[r, c]
            rgba = (int(pixel[0]), int(pixel[1]), int(pixel[2]), 255 if pixel[3] >= 128 else 0)
            row.append(rgba)
        grid.append(row)

    return grid_to_half_blocks(np.array(grid, dtype=np.uint8))


color_regex = re.compile(r'\x1b\[38;2;(\d+);(\d+);(\d+)m')

def parse_full_block_art(content):
    lines = content.strip('\n').split('\n')
    grid = []
    for line in lines:
        row = []
        cur_color = (0, 0, 0)
        idx = 0
        while idx < len(line):
            if line[idx] == '\x1b':
                m = color_regex.match(line, idx)
                if m:
                    cur_color = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
                    idx = m.end()
                    continue
                elif line[idx:idx+4] == '\x1b[0m':
                    idx += 4
                    continue
                else:
                    end_m = line.find('m', idx)
                    if end_m != -1:
                        idx = end_m + 1
                    else:
                        idx += 1
                    continue
            char = line[idx]
            if char == ' ':
                row.append((0, 0, 0, 0))
            elif char == '█':
                row.append((cur_color[0], cur_color[1], cur_color[2], 255))
            idx += 1
        undoubled_row = []
        for c in range(0, len(row), 2):
            undoubled_row.append(row[c])
        grid.append(undoubled_row)
    return np.array(grid, dtype=np.uint8)


def downscale_nearest(grid, target_h=16):
    h, w, _ = grid.shape
    if h <= target_h:
        return grid
    scale = target_h / float(h)
    new_h = int(round(h * scale))
    new_w = max(1, int(round(w * scale)))
    r_idx = np.clip((np.arange(new_h) / scale).astype(int), 0, h - 1)
    c_idx = np.clip((np.arange(new_w) / scale).astype(int), 0, w - 1)
    return grid[r_idx[:, None], c_idx]


def grid_to_half_blocks(grid_arr):
    num_rows, num_cols, _ = grid_arr.shape
    grid = grid_arr.tolist()
    if num_rows % 2 != 0:
        grid.append([[0, 0, 0, 0]] * num_cols)
        num_rows += 1

    out = []
    for r in range(0, num_rows, 2):
        row_top = grid[r]
        row_bot = grid[r + 1] if r + 1 < num_rows else [[0, 0, 0, 0]] * num_cols
        line_chars = []
        cur_fg = None
        cur_bg = None

        for c in range(num_cols):
            top = row_top[c] if c < len(row_top) else [0, 0, 0, 0]
            bot = row_bot[c] if c < len(row_bot) else [0, 0, 0, 0]

            t_col, t_a = top[:3], top[3]
            b_col, b_a = bot[:3], bot[3]

            if t_a == 0 and b_a == 0:
                if cur_bg is not None:
                    line_chars.append('\x1b[49m')
                    cur_bg = None
                line_chars.append(' ')
            elif t_a != 0 and b_a == 0:
                if cur_bg is not None:
                    line_chars.append('\x1b[49m')
                    cur_bg = None
                if cur_fg != tuple(t_col):
                    line_chars.append(f'\x1b[38;2;{t_col[0]};{t_col[1]};{t_col[2]}m')
                    cur_fg = tuple(t_col)
                line_chars.append('▀')
            elif t_a == 0 and b_a != 0:
                if cur_bg is not None:
                    line_chars.append('\x1b[49m')
                    cur_bg = None
                if cur_fg != tuple(b_col):
                    line_chars.append(f'\x1b[38;2;{b_col[0]};{b_col[1]};{b_col[2]}m')
                    cur_fg = tuple(b_col)
                line_chars.append('▄')
            else:
                if t_col == b_col:
                    if cur_bg is not None:
                        line_chars.append('\x1b[49m')
                        cur_bg = None
                    if cur_fg != tuple(t_col):
                        line_chars.append(f'\x1b[38;2;{t_col[0]};{t_col[1]};{t_col[2]}m')
                        cur_fg = tuple(t_col)
                    line_chars.append('█')
                else:
                    if cur_fg != tuple(t_col):
                        line_chars.append(f'\x1b[38;2;{t_col[0]};{t_col[1]};{t_col[2]}m')
                        cur_fg = tuple(t_col)
                    if cur_bg != tuple(b_col):
                        line_chars.append(f'\x1b[48;2;{b_col[0]};{b_col[1]};{b_col[2]}m')
                        cur_bg = tuple(b_col)
                    line_chars.append('▀')

        while line_chars and line_chars[-1] == ' ':
            line_chars.pop()
        if line_chars:
            out.append(''.join(line_chars) + '\x1b[0m')
        else:
            out.append('')
    return '\n' + '\n'.join(out) + '\n'


def crop_image_to_content(image):
    """Crops the image so that all non essential space is removed"""
    alpha_channel = image[:, :, 3]
    min_x, min_y = find_top_left(alpha_channel)
    cropped_half = image[min_y:, min_x:, :]

    flipped_image = np.flip(cropped_half, (0, 1))
    max_x, max_y = find_top_left(flipped_image[:, :, 3])
    full_cropped_flipped = flipped_image[max_y:, max_x:, :]

    cropped_image = np.flip(full_cropped_flipped, (0, 1))
    return cropped_image


def find_top_left(alpha_channel):
    """Finds top left corner of bounding box to crop to content and returns coordinates of top left"""
    min_values_x = alpha_channel.argmax(axis=1)
    min_values_y = alpha_channel.argmax(axis=0)
    min_x = np.min(min_values_x[min_values_x != 0])
    min_y = np.min(min_values_y[min_values_y != 0])
    return min_x, min_y


def get_color_escape(r, g, b, background=False):
    """Given rgb values give the escape sequence for printing out the color"""
    return '\033[{};2;{};{};{}m'.format(48 if background else 38, r, g, b)


def update_charalist():
    search_dir = os.path.join(output_path, 'small')
    if not os.path.exists(search_dir):
        search_dir = output_path

    names = []
    for file in os.listdir(search_dir):
        if file.endswith(".txt"):
            names.append(file[:-4])
    names.sort()

    with open(path_to_charalist, 'w') as charlist:
        for chara in names:
            charlist.write(f'{chara}\n')


if __name__ == '__main__':
    main()
