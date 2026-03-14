#!/bin/bash

# SkillHub CLI Script
# Usage: skillhub.sh [res_type] [res_name] [options]

# Ensure standard PATH is available for finding commands
export PATH="/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/bin:$PATH"

# SkillHub API URL (configure this to your SkillHub instance)
SKILLHUB_URL="{SKILLHUB_URL}"

# if SKILLHUB_URL=={SKILLHUB_URL} ,then SKILLHUB_URL=http://localhost:8000
if [ "$SKILLHUB_URL" = "{SKILLHUB_URL}" ]; then
    SKILLHUB_URL="http://localhost:5173"
fi
# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print error message
error() {
    echo -e "${RED}Error: $1${NC}" >&2
    exit 1
}

# Print success message
success() {
    echo -e "${GREEN}$1${NC}"
}

# Print warning message
warning() {
    echo -e "${YELLOW}Warning: $1${NC}"
}

# Print info message
info() {
    echo -e "${BLUE}$1${NC}"
}

# Show help and usage
show_help() {
    printf "${GREEN}SkillHub CLI Tool${NC}\n\n"
    printf "${BLUE}DESCRIPTION${NC}\n"
    printf "    A command-line interface for interacting with SkillHub gateway resources.\n"
    printf "    Supports three resource types: third-party APIs, gateway resources, and MCP servers.\n\n"
    printf "${BLUE}USAGE${NC}\n"
    printf "    skillhub.sh list [search_term]              List all skills or search by name\n"
    printf "    skillhub.sh install [skill_name]           Install a skill to local directory\n"
    printf "    skillhub.sh [res_type] [res_name] [options] Invoke a resource\n"
    printf "    skillhub.sh -h\n"
    printf "    skillhub.sh\n\n"
    printf "${BLUE}LIST COMMAND${NC}\n"
    printf "    skillhub.sh list [search_term]\n\n"
    printf "    Lists all available skills or searches by skill name.\n"
    printf "    Outputs: JSON with skill summary (id, name, description, category, tags, etc.)\n\n"
    printf "${BLUE}INSTALL COMMAND${NC}\n"
    printf "    skillhub.sh install [skill_name]\n\n"
    printf "    Downloads a skill from SkillHub and saves it to ./[skill_name]/SKILL.md\n\n"
    printf "${BLUE}ARGUMENTS${NC}\n"
    printf "    res_type        Resource type (required): third, gateway, mcp\n"
    printf "    res_name        Resource name (required): name of the resource to call\n\n"
    printf "${BLUE}OPTIONS${NC}\n"
    printf "    -method <method>    HTTP method: GET, POST, PUT, DELETE (required for third/gateway)\n"
    printf "    -path <path>        Resource access path (required for gateway)\n"
    printf "    -mcptool <tool>     MCP tool/method name (required for mcp)\n"
    printf "    -inputs <json>      JSON string of parameters (optional)\n"
    printf "    -token <token>      SkillHub API token (optional, defaults to SKILLHUB_API_KEY env var)\n"
    printf "    -timeout <seconds>  Request timeout in seconds (optional, default: 30)\n"
    printf "    -v                  Verbose mode: show curl command being executed (optional)\n\n"
    printf "${BLUE}EXAMPLES${NC}\n\n"
    printf "    ${YELLOW}# List all skills${NC}\n"
    printf "    skillhub.sh list\n\n"
    printf "    ${YELLOW}# Search skills by name${NC}\n"
    printf "    skillhub.sh list weather\n"
    printf "    skillhub.sh list ai -token your-api-token\n\n"
    printf "    ${YELLOW}# Install a skill${NC}\n"
    printf "    skillhub.sh install weather-skill\n"
    printf "    skillhub.sh install customer-support -token your-api-token\n\n"
    printf "    ${YELLOW}# Third-party API call${NC}\n"
    printf "    skillhub.sh third weather-api -method GET -inputs '{\"city\":\"Beijing\"}'\n"
    printf "    skillhub.sh third user-service -method POST -inputs '{\"name\":\"John\",\"email\":\"john@example.com\"}'\n\n"
    printf "    ${YELLOW}# Gateway resource call${NC}\n"
    printf "    skillhub.sh gateway my-api -method GET -path users/123\n"
    printf "    skillhub.sh gateway backend-api -method POST -path users -inputs '{\"name\":\"Jane\"}'\n"
    printf "    skillhub.sh gateway backend-api -method PUT -path users/123 -inputs '{\"name\":\"Jane Updated\"}'\n"
    printf "    skillhub.sh gateway backend-api -method DELETE -path users/123\n\n"
    printf "    ${YELLOW}# MCP server call${NC}\n"
    printf "    skillhub.sh mcp my-mcp-server -mcptool test -inputs '{\"name\":\"weather_tool\",\"arguments\":{\"location\":\"Tokyo\"}}'\n"
    printf "    skillhub.sh mcp my-mcp-server -mcptool tool_name2\n\n"
    printf "    ${YELLOW}# Using custom token${NC}\n"
    printf "    skillhub.sh third weather-api -method GET -inputs '{\"city\":\"Shanghai\"}' -token your-api-token-here\n\n"
    printf "${BLUE}ENVIRONMENT VARIABLES${NC}\n"
    printf "    SKILLHUB_API_KEY   Default API token if -token is not provided\n"
    printf "    SKILLHUB_URL       Override the default SkillHub URL \n\n"
    printf "${BLUE}RESOURCE TYPES${NC}\n"
    printf "    third       Third-party API resources (requires -method)\n"
    printf "    gateway     Gateway resources with path support (requires -method and -path)\n"
    printf "    mcp         MCP server resources (requires -mcptool)\n\n"
    printf "${BLUE}AUTHENTICATION${NC}\n"
    printf "    Token priority:\n"
    printf "    1. Token provided via -token option\n"
    printf "    2. SKILLHUB_API_KEY environment variable\n"
    printf "    3. Error if neither is available\n"
}

# Install a skill from SkillHub to local directory
install_skill() {
    local skill_name="$1"

    if [ -z "$skill_name" ]; then
        error "install command requires a skill name"
    fi

    # Get token: use provided token, fallback to env var
    if [ -z "$TOKEN" ]; then
        TOKEN="$SKILLHUB_API_KEY"
    fi

    # if [ -z "$TOKEN" ]; then
    #     error "No authentication token found. Please provide via -token option or set SKILLHUB_API_KEY environment variable"
    # fi

    info "Installing skill: $skill_name"

    # Define storage locations
    local skillhub_home="$HOME/.agent/skills"
    local actual_dir="$skillhub_home/$skill_name"
    local link_dir="./skills/$skill_name"

    # Create skillhub home directory if not exists
    if [ ! -d "$skillhub_home" ]; then
        mkdir -p "$skillhub_home" || error "Failed to create directory: $skillhub_home"
    fi

    # Create actual skill directory in ~/skillhub
    if [ -d "$actual_dir" ]; then
        warning "Directory $actual_dir already exists. Overwriting SKILL.md"
    else
        mkdir -p "$actual_dir" || error "Failed to create directory: $actual_dir"
    fi

    # Fetch skill content from API (install=true returns plain text)
    local api_url="$SKILLHUB_URL/api/v1/skills/$skill_name/?install=true"
    info "Fetching skill from: $api_url"

    local content
    content=$(/usr/bin/curl --max-time $TIMEOUT -s -X GET "$api_url" \
        -H "accept: text/plain" \
        -H "Authorization: Bearer $TOKEN")

    if [ $? -ne 0 ]; then
        error "Failed to fetch skill from API"
    fi

    # Check if content is empty or contains error
    if [ -z "$content" ]; then
        error "Failed to get skill content. Check if skill exists and you have access."
    fi

    # Check for JSON error response (install=true returns plain text on success)
    if echo "$content" | /usr/bin/grep -q '"detail"'; then
        error "API Error: $content"
    fi

    # Write to actual location
    echo "$content" > "$actual_dir/SKILL.md" || error "Failed to write to $actual_dir/SKILL.md"

    # Create local ./skills directory if not exists
    mkdir -p "./skills" 2>/dev/null || true

    # Create or update symbolic link
    if [ -L "$link_dir" ]; then
        # Link exists, remove it first
        rm "$link_dir" || warning "Failed to remove existing symlink: $link_dir"
    elif [ -e "$link_dir" ]; then
        # A file/directory exists (not a symlink), back it up
        warning "Backing up existing $link_dir to $link_dir.backup"
        mv "$link_dir" "$link_dir.backup" || error "Failed to backup existing directory: $link_dir"
    fi

    # Create symbolic link
    ln -s "$actual_dir" "$link_dir" || warning "Failed to create symlink: $link_dir -> $actual_dir"

    success "Skill installed successfully:"
    echo "  Actual: $actual_dir"
    if [ -L "$link_dir" ]; then
        echo "  Link:   $link_dir -> $actual_dir"
    fi
}

# List skills from SkillHub
list_skills() {
    local search_term="$1"

    # Get token: use provided token, fallback to env var
    if [ -z "$TOKEN" ]; then
        TOKEN="$SKILLHUB_API_KEY"
    fi

    # Build API URL with search parameter if provided
    local api_url="$SKILLHUB_URL/api/v1/skills/"
    if [ -n "$search_term" ]; then
        api_url="$api_url?search=$search_term"
        info "Searching for skills matching: $search_term"
    else
        info "Listing all skills"
    fi

    # Fetch skills from API
    local response
    response=$(/usr/bin/curl --max-time $TIMEOUT -s -X GET "$api_url" \
        -H "accept: application/json" \
        -H "Authorization: Bearer $TOKEN")

    if [ $? -ne 0 ]; then
        error "Failed to fetch skills from API"
    fi

    # Check for error response
    if echo "$response" | /usr/bin/grep -q '"detail"'; then
        error "API Error: $response"
    fi

    # Pretty print JSON response
    echo "$response" | /usr/bin/python3 -m json.tool 2>/dev/null || echo "$response"
}

# Parse command line arguments
RES_TYPE=""
RES_NAME=""
METHOD=""
RPATH=""
MCPTOOL=""
INPUTS=""
TOKEN=""
TIMEOUT=30  # Default timeout: 30 seconds
VERBOSE=0   # Verbose mode: 0=quiet, 1=show curl command

# Check if no arguments or -h flag
if [ $# -eq 0 ] || [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    show_help
    exit 0
fi

# Check for install command
if [ "$1" = "install" ]; then
    shift
    # Parse token option for install command
    while [ $# -gt 0 ]; do
        case "$1" in
            -token)
                if [ $# -lt 2 ]; then
                    error "Option -token requires a value"
                fi
                TOKEN="$2"
                shift 2
                ;;
            -timeout)
                if [ $# -lt 2 ]; then
                    error "Option -timeout requires a value"
                fi
                TIMEOUT="$2"
                shift 2
                ;;
            *)
                # First non-option argument is the skill name
                install_skill "$1"
                exit 0
                ;;
        esac
    done
    error "install command requires a skill name"
fi

# Check for list command
if [ "$1" = "list" ]; then
    shift
    # Parse token option for list command
    local search_term=""
    while [ $# -gt 0 ]; do
        case "$1" in
            -token)
                if [ $# -lt 2 ]; then
                    error "Option -token requires a value"
                fi
                TOKEN="$2"
                shift 2
                ;;
            -timeout)
                if [ $# -lt 2 ]; then
                    error "Option -timeout requires a value"
                fi
                TIMEOUT="$2"
                shift 2
                ;;
            *)
                # First non-option argument is the search term
                list_skills "$1"
                exit 0
                ;;
        esac
    done
    # No search term provided, list all skills
    list_skills ""
    exit 0
fi

# Parse res_type (first positional argument)
RES_TYPE="$1"
shift

# Validate res_type
if [ "$RES_TYPE" != "third" ] && [ "$RES_TYPE" != "gateway" ] && [ "$RES_TYPE" != "mcp" ]; then
    error "Invalid res_type '$RES_TYPE'. Must be one of: third, gateway, mcp"
fi

# Parse res_name (second positional argument)
if [ $# -eq 0 ]; then
    error "res_name is required"
fi
RES_NAME="$1"
shift

# Parse options
while [ $# -gt 0 ]; do
    case "$1" in
        -method)
            if [ $# -lt 2 ]; then
                error "Option -method requires a value"
            fi
            METHOD="$2"
            shift 2
            ;;
        -path)
            if [ $# -lt 2 ]; then
                error "Option -path requires a value"
            fi
            RPATH="$2"
            shift 2
            ;;
        -mcptool)
            if [ $# -lt 2 ]; then
                error "Option -mcptool requires a value"
            fi
            MCPTOOL="$2"
            shift 2
            ;;
        -inputs)
            if [ $# -lt 2 ]; then
                error "Option -inputs requires a value"
            fi
            INPUTS="$2"
            shift 2
            ;;
        -token)
            if [ $# -lt 2 ]; then
                error "Option -token requires a value"
            fi
            TOKEN="$2"
            shift 2
            ;;
        -timeout)
            if [ $# -lt 2 ]; then
                error "Option -timeout requires a value"
            fi
            TIMEOUT="$2"
            shift 2
            ;;
        -v)
            VERBOSE=1
            shift
            ;;
        *)
            error "Unknown option: $1"
            ;;
    esac
done

# Get token: use provided token, fallback to env var
if [ -z "$TOKEN" ]; then
    TOKEN="$SKILLHUB_API_KEY"
fi

if [ -z "$TOKEN" ]; then
    error "No authentication token found. Please provide via -token option or set SKILLHUB_API_KEY environment variable"
fi

# Override SKILLHUB_URL from environment if set
# if [ -n "$SKILLHUB_URL" ] && [ "$SKILLHUB_URL" != "http://localhost:8000" ]; then
#     info "Using custom SKILLHUB_URL: $SKILLHUB_URL"
# fi

# Validate required parameters based on res_type
case "$RES_TYPE" in
    third)
        if [ -z "$METHOD" ]; then
            error "res_type 'third' requires -method option (GET, POST, PUT, DELETE)"
        fi
        # Validate method and convert to uppercase (portable way)
        case "$METHOD" in
            [gG][eE][tT])   METHOD="GET" ;;
            [pP][oO][sS][tT]) METHOD="POST" ;;
            [pP][uU][tT])    METHOD="PUT" ;;
            [dD][eE][lL][eE][tT][eE]) METHOD="DELETE" ;;
            *) error "Invalid method '$METHOD'. Must be one of: GET, POST, PUT, DELETE" ;;
        esac
        ;;
    gateway)
        if [ -z "$METHOD" ]; then
            error "res_type 'gateway' requires -method option (GET, POST, PUT, DELETE)"
        fi
        if [ -z "$RPATH" ]; then
            error "res_type 'gateway' requires -path option"
        fi
        # Validate method and convert to uppercase (portable way)
        case "$METHOD" in
            [gG][eE][tT])   METHOD="GET" ;;
            [pP][oO][sS][tT]) METHOD="POST" ;;
            [pP][uU][tT])    METHOD="PUT" ;;
            [dD][eE][lL][eE][tT][eE]) METHOD="DELETE" ;;
            *) error "Invalid method '$METHOD'. Must be one of: GET, POST, PUT, DELETE" ;;
        esac
        ;;
    mcp)
        if [ -z "$MCPTOOL" ]; then
            error "res_type 'mcp' requires -mcptool option"
        fi
        ;;
esac

# Convert METHOD to lowercase for URL path (portable way)
METHOD_LOWER=""
case "$METHOD" in
    GET)    METHOD_LOWER="get" ;;
    POST)   METHOD_LOWER="post" ;;
    PUT)    METHOD_LOWER="put" ;;
    DELETE) METHOD_LOWER="delete" ;;
esac

# URL encode a string (percent encoding) - bash 3.x compatible
url_encode() {
    local string="$1"
    local encoded=""
    local length=${#string}
    local pos=0
    local c=""

    while [ $pos -lt $length ]; do
        c="${string:$pos:1}"
        case "$c" in
            [a-zA-Z0-9._~-]) encoded="$encoded$c" ;;
            ' ') encoded="$encoded+" ;;
            *)
                # Get ASCII value and convert to hex
                local char_val
                char_val=$(printf '%d' "'$c")
                encoded="$encoded%$(printf '%02X' $char_val)"
                ;;
        esac
        pos=$((pos+1))
    done
    echo "$encoded"
}

# Convert JSON to URL query parameters (simplified parser for flat JSON)
json_to_query_params() {
    local json="$1"
    local result=""
    local key=""
    local value=""
    local state="start"  # start, key, colon, value, done
    local i=0
    local len=${#json}
    local char=""

    # Remove outer braces and whitespace
    json="${json#\{}"
    json="${json%\}}"
    json=$(echo "$json" | /usr/bin/sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

    # Process each character
    while [ $i -lt $len ]; do
        char="${json:$i:1}"

        case "$char" in
            '"')
                case "$state" in
                    start|comma)
                        state="key"
                        key=""
                        ;;
                    key)
                        # End of key, look for colon
                        state="after_key"
                        ;;
                    value)
                        # End of value, add pair
                        local ek=$(url_encode "$key")
                        local ev=$(url_encode "$value")
                        if [ -n "$result" ]; then
                            result="$result&$ek=$ev"
                        else
                            result="$ek=$ev"
                        fi
                        key=""
                        value=""
                        state="done"
                        ;;
                esac
                ;;
            ':')
                if [ "$state" = "after_key" ]; then
                    state="before_value"
                fi
                ;;
            ',')
                if [ "$state" = "done" ]; then
                    state="comma"
                fi
                ;;
            *)
                case "$state" in
                    key)
                        key="$key$char"
                        ;;
                    value)
                        value="$value$char"
                        ;;
                    before_value)
                        state="value"
                        value="$char"
                        ;;
                esac
                ;;
        esac
        i=$((i+1))
    done

    # Handle last pair
    if [ -n "$key" ]; then
        local ek=$(url_encode "$key")
        local ev=$(url_encode "$value")
        if [ -n "$result" ]; then
            result="$result&$ek=$ev"
        else
            result="$ek=$ev"
        fi
    fi

    echo "$result"
}

# Build URL and execute curl based on res_type
case "$RES_TYPE" in
    third)
        URL="$SKILLHUB_URL/api/v1/gateway/$RES_NAME/$METHOD_LOWER"
        #info "Calling: $METHOD $URL"

        # Build curl command with timeout
        CURL_CMD="/usr/bin/curl --max-time $TIMEOUT -L -X '$METHOD' '$URL'"
        CURL_CMD="$CURL_CMD -H 'Content-Type: application/json'"
        CURL_CMD="$CURL_CMD -H 'Authorization: Bearer $TOKEN'"

        # Add inputs as query params for GET/DELETE, or as body for other methods
        if [ -n "$INPUTS" ]; then
            if [ "$METHOD" = "GET" ] || [ "$METHOD" = "DELETE" ]; then
                # Convert JSON to URL-encoded query parameters
                QUERY_PARAMS=$(json_to_query_params "$INPUTS")
                if [ -n "$QUERY_PARAMS" ]; then
                    URL="$URL?$QUERY_PARAMS"
                    CURL_CMD="/usr/bin/curl --max-time $TIMEOUT -L -X '$METHOD' '$URL' -H 'Content-Type: application/json' -H 'Authorization: Bearer $TOKEN'"

                fi
            else
                CURL_CMD="$CURL_CMD -d '$INPUTS'"
            fi
        fi

        # Execute curl command
        if [ $VERBOSE -eq 1 ]; then
            info "$CURL_CMD"
        fi
        eval $CURL_CMD
        ;;

    gateway)
        # Remove leading slash from RPATH if present to avoid double slashes
        CLEAN_PATH="${RPATH#/}"
        URL="$SKILLHUB_URL/api/v1/gateway/$RES_NAME/$CLEAN_PATH"
        #info "Calling: $METHOD $URL"
        # Build curl command with timeout
        CURL_CMD="/usr/bin/curl --max-time $TIMEOUT -L -X '$METHOD' '$URL'"
        CURL_CMD="$CURL_CMD -H 'Content-Type: application/json'"
        CURL_CMD="$CURL_CMD -H 'Authorization: Bearer $TOKEN'"

        # Add inputs as query params for GET, or as body for other methods
        if [ -n "$INPUTS" ]; then
            if [ "$METHOD" = "GET" ] || [ "$METHOD" = "DELETE" ]; then
                # Add inputs as query parameters (URL encode the JSON string)
                QUERY_PARAMS=$(json_to_query_params "$INPUTS")
                URL="$URL?$QUERY_PARAMS"
                CURL_CMD="/usr/bin/curl --max-time $TIMEOUT -L -X '$METHOD' '$URL' -H 'Content-Type: application/json' -H 'Authorization: Bearer $TOKEN'"
            else
                CURL_CMD="$CURL_CMD -d '$INPUTS'"
            fi
        fi

        # Execute curl command
        if [ $VERBOSE -eq 1 ]; then
            info "$CURL_CMD"
        fi
        eval $CURL_CMD
        ;;

    mcp)
        URL="$SKILLHUB_URL/api/v1/gateway/$RES_NAME/mcp"
        #info "Calling MCP: POST $URL (method: $MCPTOOL)"

        # Build request body
        if [ -n "$INPUTS" ]; then
            REQUEST_BODY="{\"method\": \"${MCPTOOL}\", \"params\": ${INPUTS}}"
        else
            REQUEST_BODY="{\"method\": \"${MCPTOOL}\", \"params\": {}}"
        fi

        # Execute curl command with timeout
        CURL_CMD="/usr/bin/curl --max-time $TIMEOUT -L -X 'POST' '$URL' -H 'Content-Type: application/json' -H 'Authorization: Bearer $TOKEN' -d '$REQUEST_BODY'"
        if [ $VERBOSE -eq 1 ]; then
            info "$CURL_CMD"
        fi
        eval $CURL_CMD
        ;;
esac
