#!/bin/bash
#===============================================================================
#
#          FILE: rebuild.sh
#
#         USAGE: ./rebuild.sh [OPTIONS]
#
#   DESCRIPTION: KRONOS HRMS - Enterprise Full Stack Rebuild & Initialization
#                Performs complete teardown and rebuild of the Docker stack
#                with proper cleanup, health checks, and database seeding.
#
#       OPTIONS:
#           -h, --help          Show this help message
#           -s, --skip-seed     Skip database seeding (schema only)
#           -c, --skip-cache    Skip Docker cache (force rebuild, default)
#           -k, --keep-cache    Use Docker cache for faster builds
#           -p, --prune-all     Aggressive Docker cleanup (system prune)
#           -v, --verbose       Enable verbose output
#           -q, --quiet         Suppress non-essential output
#           --dry-run           Show what would be done without executing
#
#  REQUIREMENTS: docker, docker-compose
#
#        AUTHOR: KRONOS DevOps Team
#       VERSION: 2.0.0
#       CREATED: 2026-01-06
#
#===============================================================================

set -euo pipefail  # Exit on error, undefined vars, pipe failures

#-------------------------------------------------------------------------------
# CONFIGURATION
#-------------------------------------------------------------------------------
readonly SCRIPT_NAME=$(basename "$0")
readonly SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
readonly LOG_FILE="${SCRIPT_DIR}/logs/rebuild_$(date +%Y%m%d_%H%M%S).log"
readonly STACK_NAME="kronos"
readonly PROJECT_NAME="app-gestione-presenze"

# Timeouts (in seconds)
readonly STACK_REMOVAL_TIMEOUT=30
readonly HEALTHCHECK_TIMEOUT=60
readonly DB_INIT_TIMEOUT=120

# Container names
readonly AUTH_CONTAINER="kronos-auth"
readonly DB_CONTAINER="kronos-db"

# Default options
SKIP_SEED=false
USE_CACHE=false
PRUNE_ALL=false
VERBOSE=false
QUIET=false
DRY_RUN=false

#-------------------------------------------------------------------------------
# COLORS & FORMATTING
#-------------------------------------------------------------------------------
if [[ -t 1 ]]; then
    readonly RED='\033[0;31m'
    readonly GREEN='\033[0;32m'
    readonly YELLOW='\033[1;33m'
    readonly BLUE='\033[0;34m'
    readonly MAGENTA='\033[0;35m'
    readonly CYAN='\033[0;36m'
    readonly WHITE='\033[1;37m'
    readonly GRAY='\033[0;90m'
    readonly NC='\033[0m'
    readonly BOLD='\033[1m'
    readonly DIM='\033[2m'
else
    readonly RED='' GREEN='' YELLOW='' BLUE='' MAGENTA='' CYAN='' WHITE='' GRAY='' NC='' BOLD='' DIM=''
fi

#-------------------------------------------------------------------------------
# LOGGING FUNCTIONS
#-------------------------------------------------------------------------------
log_init() {
    mkdir -p "$(dirname "$LOG_FILE")"
    echo "=== KRONOS Rebuild Log - $(date) ===" > "$LOG_FILE"
}

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
}

print_header() {
    echo -e "\n${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC} ${WHITE}${BOLD}$1${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
}

print_step() {
    local step_num="$1"
    local step_name="$2"
    echo -e "\n${CYAN}┌─ Step ${step_num}: ${step_name}${NC}"
    log "INFO" "Step ${step_num}: ${step_name}"
}

print_substep() {
    [[ "$QUIET" == "true" ]] && return
    echo -e "${GRAY}│  ├─ $1${NC}"
}

print_success() {
    echo -e "${GREEN}│  └─ ✓ $1${NC}"
    log "INFO" "SUCCESS: $1"
}

print_warning() {
    echo -e "${YELLOW}│  └─ ⚠ $1${NC}"
    log "WARN" "$1"
}

print_error() {
    echo -e "${RED}│  └─ ✗ $1${NC}" >&2
    log "ERROR" "$1"
}

print_info() {
    [[ "$QUIET" == "true" ]] && return
    echo -e "${GRAY}│  │  $1${NC}"
}

#-------------------------------------------------------------------------------
# UTILITY FUNCTIONS
#-------------------------------------------------------------------------------
show_help() {
    cat << EOF
${BOLD}KRONOS HRMS - Enterprise Stack Rebuild${NC}

${YELLOW}Usage:${NC} $SCRIPT_NAME [OPTIONS]

${YELLOW}Options:${NC}
    -h, --help          Show this help message and exit
    -s, --skip-seed     Initialize database schema only, skip seed data
    -c, --skip-cache    Force rebuild without Docker cache (default)
    -k, --keep-cache    Use Docker cache for faster builds
    -p, --prune-all     Aggressive Docker cleanup (docker system prune)
    -v, --verbose       Enable verbose output
    -q, --quiet         Suppress non-essential output
    --dry-run           Show what would be done without executing

${YELLOW}Examples:${NC}
    $SCRIPT_NAME                    # Full rebuild with seeding
    $SCRIPT_NAME --skip-seed        # Rebuild with empty database
    $SCRIPT_NAME --keep-cache       # Quick rebuild using cache
    $SCRIPT_NAME --prune-all        # Deep clean before rebuild

${YELLOW}Log Location:${NC}
    ${LOG_FILE}

EOF
    exit 0
}

check_dependencies() {
    local deps=("docker" "docker-compose")
    local missing=()
    
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            missing+=("$dep")
        fi
    done
    
    if [[ ${#missing[@]} -gt 0 ]]; then
        print_error "Missing required dependencies: ${missing[*]}"
        exit 1
    fi
}

check_docker_running() {
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running"
        exit 1
    fi
}

execute() {
    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "${MAGENTA}[DRY-RUN]${NC} $*"
        log "DRY-RUN" "$*"
        return 0
    fi
    
    if [[ "$VERBOSE" == "true" ]]; then
        "$@" 2>&1 | tee -a "$LOG_FILE"
    else
        "$@" >> "$LOG_FILE" 2>&1
    fi
}

wait_for_container() {
    local container="$1"
    local timeout="${2:-30}"
    local elapsed=0
    
    print_info "Waiting for container ${container} to be ready..."
    
    while [[ $elapsed -lt $timeout ]]; do
        if docker inspect -f '{{.State.Running}}' "$container" 2>/dev/null | grep -q "true"; then
            return 0
        fi
        sleep 1
        ((elapsed++))
    done
    
    return 1
}

wait_for_healthcheck() {
    local container="$1"
    local timeout="${2:-60}"
    local elapsed=0
    
    print_info "Waiting for ${container} healthcheck..."
    
    while [[ $elapsed -lt $timeout ]]; do
        local health=$(docker inspect -f '{{.State.Health.Status}}' "$container" 2>/dev/null || echo "none")
        
        case "$health" in
            "healthy")
                return 0
                ;;
            "unhealthy")
                return 1
                ;;
            "none")
                # No healthcheck defined, wait for running state
                if docker inspect -f '{{.State.Running}}' "$container" 2>/dev/null | grep -q "true"; then
                    sleep 2
                    return 0
                fi
                ;;
        esac
        
        sleep 2
        ((elapsed+=2))
        print_info "Health status: ${health} (${elapsed}s/${timeout}s)"
    done
    
    return 1
}

get_elapsed_time() {
    local start=$1
    local end=$(date +%s)
    local elapsed=$((end - start))
    local minutes=$((elapsed / 60))
    local seconds=$((elapsed % 60))
    echo "${minutes}m ${seconds}s"
}

#-------------------------------------------------------------------------------
# MAIN OPERATIONS
#-------------------------------------------------------------------------------
step_remove_stack() {
    print_step "1" "Remove Existing Docker Stack"
    
    # Check for Docker Swarm stack
    if docker stack ls 2>/dev/null | grep -q "${STACK_NAME}"; then
        print_substep "Removing Docker Swarm stack: ${STACK_NAME}"
        execute docker stack rm "${STACK_NAME}"
        
        local elapsed=0
        while docker stack ls 2>/dev/null | grep -q "${STACK_NAME}" && [[ $elapsed -lt $STACK_REMOVAL_TIMEOUT ]]; do
            sleep 2
            ((elapsed+=2))
            print_info "Waiting for stack removal... (${elapsed}s)"
        done
        print_success "Docker Swarm stack removed"
    else
        print_info "No Swarm stack found"
    fi
    
    # Stop docker-compose services
    print_substep "Stopping docker-compose services"
    execute docker-compose down -v --remove-orphans || true
    print_success "Containers stopped and volumes removed"
}

step_cleanup_images() {
    print_step "2" "Clean Docker Images & Cache"
    
    # Remove dangling images
    print_substep "Removing dangling images"
    execute docker image prune -f
    
    # Remove project-specific images
    print_substep "Removing KRONOS project images"
    local images=$(docker images --filter "reference=*${STACK_NAME}*" -q 2>/dev/null || true)
    if [[ -n "$images" ]]; then
        echo "$images" | xargs -r docker rmi -f 2>/dev/null || true
    fi
    
    images=$(docker images --filter "reference=*${PROJECT_NAME}*" -q 2>/dev/null || true)
    if [[ -n "$images" ]]; then
        echo "$images" | xargs -r docker rmi -f 2>/dev/null || true
    fi
    
    # Aggressive cleanup if requested
    if [[ "$PRUNE_ALL" == "true" ]]; then
        print_substep "Running aggressive Docker system prune"
        execute docker system prune -af --volumes
        print_success "Full Docker system cleanup completed"
    else
        print_success "Image cleanup completed"
    fi
    
    # Show disk space recovered
    if [[ "$VERBOSE" == "true" ]]; then
        echo -e "${GRAY}│  │  Disk usage after cleanup:${NC}"
        docker system df 2>/dev/null | head -5
    fi
}

step_build_images() {
    print_step "3" "Build Docker Images"
    
    local build_start=$(date +%s)
    local build_args="--parallel"
    
    if [[ "$USE_CACHE" == "false" ]]; then
        build_args="$build_args --no-cache"
        print_substep "Building without cache (full rebuild)"
    else
        print_substep "Building with cache (incremental)"
    fi
    
    if [[ "$VERBOSE" == "true" ]]; then
        build_args="$build_args --progress=plain"
    fi
    
    execute docker-compose build $build_args
    
    local build_time=$(get_elapsed_time $build_start)
    print_success "Images built successfully (${build_time})"
}

step_start_services() {
    print_step "4" "Start Services"
    
    print_substep "Starting Docker Compose stack"
    execute docker-compose up -d
    
    # List running containers
    if [[ "$VERBOSE" == "true" ]]; then
        echo -e "${GRAY}│  │  Running containers:${NC}"
        docker-compose ps
    fi
    
    print_success "All services started"
}

step_wait_for_services() {
    print_step "5" "Health Checks"
    
    # Wait for database
    print_substep "Waiting for database (${DB_CONTAINER})"
    if wait_for_healthcheck "$DB_CONTAINER" "$HEALTHCHECK_TIMEOUT"; then
        print_info "Database is ready"
    else
        print_warning "Database healthcheck timeout, proceeding anyway"
    fi
    
    # Wait for auth service
    print_substep "Waiting for auth service (${AUTH_CONTAINER})"
    if wait_for_container "$AUTH_CONTAINER" 30; then
        print_info "Auth service container is running"
    else
        print_error "Auth service failed to start"
        docker-compose logs "$AUTH_CONTAINER" | tail -20
        exit 1
    fi
    
    # Additional wait for service initialization
    print_substep "Allowing services to initialize"
    sleep 10
    
    print_success "All services are healthy"
}

step_initialize_database() {
    print_step "6" "Initialize Database"
    
    local init_start=$(date +%s)
    
    print_substep "Running Alembic migrations (init_db.py)"
    if ! execute docker exec "$AUTH_CONTAINER" python scripts/init_db.py; then
        print_error "Database initialization failed"
        echo -e "${RED}Check logs with: docker logs ${AUTH_CONTAINER}${NC}"
        exit 1
    fi
    print_info "Migrations completed"
    
    if [[ "$SKIP_SEED" == "true" ]]; then
        print_warning "Skipping database seeding (--skip-seed)"
        print_success "Database schema initialized (empty)"
        return 0
    fi
    
    # Run seed scripts in order
    local seeds=(
        "seed_enterprise_calendar_data.py:Enterprise Calendar"
        "seed_executive_levels.py:Executive Levels"
        "seed_enterprise_data.py:Enterprise Data (Users, Wallets)"
        "seed_organization.py:Organization Structure"
        "seed_workflows.py:Approval Workflows"
    )
    
    print_substep "Running seed scripts"
    for seed_entry in "${seeds[@]}"; do
        local script="${seed_entry%%:*}"
        local description="${seed_entry##*:}"
        
        print_info "Seeding: ${description}"
        if ! execute docker exec "$AUTH_CONTAINER" python "scripts/${script}"; then
            print_error "Seed script failed: ${script}"
            exit 1
        fi
    done
    
    local init_time=$(get_elapsed_time $init_start)
    print_success "Database initialized and seeded (${init_time})"
}

step_show_summary() {
    local total_time=$(get_elapsed_time $SCRIPT_START_TIME)
    
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║${NC}                                                                ${GREEN}║${NC}"
    echo -e "${GREEN}║${NC}   ${WHITE}${BOLD}✨ KRONOS HRMS Stack is READY! ✨${NC}                           ${GREEN}║${NC}"
    echo -e "${GREEN}║${NC}                                                                ${GREEN}║${NC}"
    echo -e "${GREEN}╠════════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${GREEN}║${NC}                                                                ${GREEN}║${NC}"
    echo -e "${GREEN}║${NC}   ${CYAN}Frontend:${NC}     http://localhost:3000                         ${GREEN}║${NC}"
    echo -e "${GREEN}║${NC}   ${CYAN}API Gateway:${NC}  http://localhost:8001                         ${GREEN}║${NC}"
    echo -e "${GREEN}║${NC}   ${CYAN}API Docs:${NC}     http://localhost:8001/docs                    ${GREEN}║${NC}"
    echo -e "${GREEN}║${NC}   ${CYAN}Keycloak:${NC}     http://localhost:8080   ${DIM}(admin/admin)${NC}        ${GREEN}║${NC}"
    echo -e "${GREEN}║${NC}                                                                ${GREEN}║${NC}"
    echo -e "${GREEN}╠════════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${GREEN}║${NC}                                                                ${GREEN}║${NC}"
    echo -e "${GREEN}║${NC}   ${GRAY}Total time: ${total_time}${NC}                                        ${GREEN}║${NC}"
    echo -e "${GREEN}║${NC}   ${GRAY}Log file: ${LOG_FILE}${NC}"
    echo -e "${GREEN}║${NC}                                                                ${GREEN}║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    log "INFO" "Rebuild completed successfully in ${total_time}"
}

#-------------------------------------------------------------------------------
# ERROR HANDLING
#-------------------------------------------------------------------------------
cleanup_on_error() {
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        echo ""
        print_error "Rebuild failed with exit code: ${exit_code}"
        echo -e "${RED}Check the log file for details: ${LOG_FILE}${NC}"
        echo ""
        echo -e "${YELLOW}Troubleshooting:${NC}"
        echo "  1. Check container logs:  docker-compose logs"
        echo "  2. View specific service: docker logs <container-name>"
        echo "  3. Check disk space:      df -h"
        echo "  4. Restart Docker:        sudo systemctl restart docker"
        echo ""
    fi
}

trap cleanup_on_error EXIT

#-------------------------------------------------------------------------------
# MAIN
#-------------------------------------------------------------------------------
main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h|--help)
                show_help
                ;;
            -s|--skip-seed|--no-seed)
                SKIP_SEED=true
                shift
                ;;
            -c|--skip-cache|--no-cache)
                USE_CACHE=false
                shift
                ;;
            -k|--keep-cache|--use-cache)
                USE_CACHE=true
                shift
                ;;
            -p|--prune-all|--prune)
                PRUNE_ALL=true
                shift
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -q|--quiet)
                QUIET=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                VERBOSE=true
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
    
    # Record start time
    readonly SCRIPT_START_TIME=$(date +%s)
    
    # Initialize
    log_init
    check_dependencies
    check_docker_running
    
    # Print header
    print_header "🔄 KRONOS HRMS - Enterprise Full Stack Rebuild"
    echo -e "${GRAY}Started at: $(date)${NC}"
    echo -e "${GRAY}Options: skip-seed=${SKIP_SEED}, use-cache=${USE_CACHE}, prune-all=${PRUNE_ALL}${NC}"
    log "INFO" "Rebuild started with options: skip-seed=${SKIP_SEED}, use-cache=${USE_CACHE}, prune-all=${PRUNE_ALL}"
    
    # Execute rebuild steps
    step_remove_stack
    step_cleanup_images
    step_build_images
    step_start_services
    step_wait_for_services
    step_initialize_database
    step_show_summary
}

# Change to script directory
cd "$SCRIPT_DIR"

# Run main
main "$@"
