#!/bin/bash

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

test_service() {
  local name=$1
  local url=$2
  local count=${3:-10}

  start=$(date +%s.%N)

  for i in $(seq 1 $count); do
    curl -s $url > /dev/null 2>&1 &
  done
  wait

  end=$(date +%s.%N)
  duration=$(echo "$end - $start" | bc)
  rps=$(echo "scale=1; $count / $duration" | bc)

  printf "  %-30s | %5.2fs | RPS: %4.1f\n" "$name" "$duration" "$rps"
}

# Default values
COUNT=10
ENDPOINT="/slow"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    -n|--count)
      COUNT="$2"
      shift 2
      ;;
    -e|--endpoint)
      ENDPOINT="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [-n COUNT] [-e ENDPOINT]"
      exit 1
      ;;
  esac
done

echo -e "${GREEN}Testing with $COUNT concurrent requests to $ENDPOINT${NC}"
echo ""

test_service "Flask WSGI (sync)" "http://localhost:5001${ENDPOINT}" $COUNT
test_service "Flask WSGI + async (trap)" "http://localhost:5002${ENDPOINT}" $COUNT
test_service "Flask ASGI + async" "http://localhost:5003${ENDPOINT}" $COUNT
test_service "Quart native" "http://localhost:5004${ENDPOINT}" $COUNT

echo ""
echo -e "${YELLOW}💡 Try different loads:${NC}"
echo "  ./test-concurrent.sh -n 50     # 50 concurrent requests"
echo "  ./test-concurrent.sh -n 100    # 100 concurrent requests"
echo ""
echo -e "${YELLOW}💡 Try different endpoints:${NC}"
echo "  ./test-concurrent.sh -e /multi-io"
echo "  ./test-concurrent.sh -e /db-simulation"
