#!/usr/bin/env python3
"""Scale a colorscript text file to an arbitrary number of terminal lines."""
import sys
import os
import re
import numpy as np

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

def downscale_nearest(grid, target_h):
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

def main():
    if len(sys.argv) < 3:
        print("Usage: scale_art.py <filepath> <target_lines>")
        sys.exit(1)

    filepath = sys.argv[1]
    target_lines = int(sys.argv[2])
    target_pixels = target_lines * 2

    with open(filepath, 'r') as fp:
        content = fp.read()

    grid = parse_full_block_art(content)
    scaled_grid = downscale_nearest(grid, target_pixels)
    art = grid_to_half_blocks(scaled_grid)
    sys.stdout.write(art)

if __name__ == '__main__':
    main()
