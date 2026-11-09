#!/bin/sh

# Checking the OS so as to use mac specific utilities on MacOS
OS=$(uname)
if [ "$OS" = 'Darwin' ]; then
    PROGRAM=$(greadlink -f "$0")
else
    PROGRAM=$(readlink -f "$0")
fi

PROGRAM_DIR=$(dirname "$PROGRAM")
# directory where all the art files exist
CHARART_DIR="$PROGRAM_DIR/colorscripts"
# formatting for the help strings
fmt_help="  %-20s\t%-54s\n"

_help(){
    # Function that prints out the help text
    echo "Description: CLI utility to print out unicode image of an anime in your shell"
    echo ""
    echo "Usage: anime-colorscripts [OPTION] [ANIME NAME]"
    printf "${fmt_help}" \
        "-h, --help, help" "Print this help." \
        "-l, --list, list" "Print list of all anime" \
        "-s, --small" "Show small version of anime (~10 lines, default)" \
        "-m, --medium" "Show medium version of anime (~16 lines)" \
        "-b, --big" "Show large / big version of anime (~32 lines)" \
        "-H, --height <N>" "Set custom terminal height in lines (e.g. 10, 12, 16)" \
        "-r, --random, random" "Show a random anime. This flag can optionally be
                        followed by character / anime names (eg. miku, lumi, naruto)
                        this will choose random anime character between all possible
                        outcomes" \
        "-n, --name" "Select anime by name."
    echo "Examples: anime-colorscripts --name 5235-kanna-ok"
    echo "          anime-colorscripts -r"
    echo "          anime-colorscripts -r --height 10"
    echo "          anime-colorscripts -r -m"
    echo "          anime-colorscripts -r -b"
    echo "          anime-colorscripts -r miku"
    echo "          anime-colorscripts -r -b miku naruto"
}

_list_anime_names(){
    if [ -t 1 ] && command -v less >/dev/null 2>&1; then
        cat "$PROGRAM_DIR/charalist.txt" | less
    else
        cat "$PROGRAM_DIR/charalist.txt"
    fi
}

_print_art_file(){
    target_file=$1
    if [ -n "$custom_height" ] && [ "$custom_height" != "10" ] && [ "$custom_height" != "16" ] && [ "$custom_height" != "32" ]; then
        # Dynamically scale from large source
        fname=$(basename "$target_file")
        large_source="$CHARART_DIR/large/$fname"
        if [ ! -f "$large_source" ]; then
            large_source="$target_file"
        fi
        if [ -f "$PROGRAM_DIR/src/generator/scale_art.py" ]; then
            python3 "$PROGRAM_DIR/src/generator/scale_art.py" "$large_source" "$custom_height"
        else
            cat "$target_file"
        fi
    else
        cat "$target_file"
    fi
}

_show_random_anime(){
    if [ -z "$random_filters" ]; then
        if [ "$OS" = 'Darwin' ]; then
            random_file=$(find "$ART_DIR" -maxdepth 1 -type f -name "*.txt" 2>/dev/null | gshuf -n 1)
        else
            random_file=$(find "$ART_DIR" -maxdepth 1 -type f -name "*.txt" 2>/dev/null | shuf -n 1)
        fi

        if [ -z "$random_file" ]; then
            echo "No anime found in $ART_DIR"
            exit 1
        fi

        echo "$(basename "$random_file" .txt)"
        _print_art_file "$random_file"
    else
        # Filtered random
        if [ "$OS" = 'Darwin' ]; then
            random_file=$(_show_random_filtered $random_filters | gshuf -n 1)
        else
            random_file=$(_show_random_filtered $random_filters | shuf -n 1)
        fi

        if [ -z "$random_file" ]; then
            echo "Invalid anime"
            exit 1
        fi

        echo "$(basename "$random_file" .txt)"
        _print_art_file "$random_file"
    fi
}

_show_random_filtered(){
    for var in "$@"; do
        find "$ART_DIR" -maxdepth 1 -type f -iname "*$var*.txt" 2>/dev/null
    done
}

_show_anime_by_name(){
    anime_name=$1
    if [ -z "$anime_name" ]; then
        echo "Please specify an anime name."
        exit 1
    fi

    target_file=""
    if [ -f "$ART_DIR/$anime_name.txt" ]; then
        target_file="$ART_DIR/$anime_name.txt"
    elif [ -f "$ART_DIR/$anime_name" ]; then
        target_file="$ART_DIR/$anime_name"
    else
        target_file=$(find "$ART_DIR" -maxdepth 1 -type f -iname "*$anime_name*.txt" 2>/dev/null | head -n 1)
    fi

    if [ -n "$target_file" ] && [ -f "$target_file" ]; then
        echo "$(basename "$target_file" .txt)"
        _print_art_file "$target_file"
    else
        echo "Invalid anime"
        exit 1
    fi
}

# Default settings
size="small"
action=""
anime_name=""
random_filters=""
custom_height=""

# If no arguments given, display help
if [ $# -eq 0 ]; then
    _help
    exit 0
fi

# Parsing command line arguments
while [ $# -gt 0 ]; do
    case "$1" in
        -h|--help|help)
            action="help"
            shift
            ;;
        -l|--list|list)
            action="list"
            shift
            ;;
        -s|--small|small)
            size="small"
            custom_height=""
            shift
            ;;
        -m|--medium|medium)
            size="medium"
            custom_height=""
            shift
            ;;
        -b|--big|--large|big|large)
            size="large"
            custom_height=""
            shift
            ;;
        -H|--height)
            shift
            if [ $# -gt 0 ]; then
                custom_height="$1"
                if [ "$custom_height" = "10" ]; then
                    size="small"
                elif [ "$custom_height" = "16" ]; then
                    size="medium"
                elif [ "$custom_height" = "32" ]; then
                    size="large"
                fi
                shift
            fi
            ;;
        -r|--random|random)
            action="random"
            shift
            while [ $# -gt 0 ]; do
                case "$1" in
                    -b|--big|--large|big|large)
                        size="large"
                        custom_height=""
                        shift
                        ;;
                    -m|--medium|medium)
                        size="medium"
                        custom_height=""
                        shift
                        ;;
                    -s|--small|small)
                        size="small"
                        custom_height=""
                        shift
                        ;;
                    -H|--height)
                        shift
                        if [ $# -gt 0 ]; then
                            custom_height="$1"
                            if [ "$custom_height" = "10" ]; then
                                size="small"
                            elif [ "$custom_height" = "16" ]; then
                                size="medium"
                            elif [ "$custom_height" = "32" ]; then
                                size="large"
                            fi
                            shift
                        fi
                        ;;
                    -*)
                        break
                        ;;
                    *)
                        random_filters="$random_filters $1"
                        shift
                        ;;
                esac
            done
            ;;
        -n|--name|name)
            action="name"
            shift
            if [ $# -gt 0 ] && [ "${1#-}" = "$1" ]; then
                anime_name="$1"
                shift
            fi
            ;;
        -*)
            echo "Input error: unknown option $1"
            _help
            exit 1
            ;;
        *)
            if [ -z "$action" ]; then
                action="name"
                anime_name="$1"
            elif [ "$action" = "name" ] && [ -z "$anime_name" ]; then
                anime_name="$1"
            fi
            shift
            ;;
    esac
done

# Resolve ART_DIR based on selected size
ART_DIR="$CHARART_DIR"
if [ -d "$CHARART_DIR/$size" ]; then
    ART_DIR="$CHARART_DIR/$size"
fi

case "$action" in
    help)
        _help
        ;;
    list)
        _list_anime_names
        ;;
    random)
        _show_random_anime
        ;;
    name)
        _show_anime_by_name "$anime_name"
        ;;
    *)
        _help
        ;;
esac
