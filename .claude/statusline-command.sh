#!/usr/bin/env bash
# Claude Code status line: model name, context % used, context tokens remaining

input=$(cat)

model=$(echo "$input" | jq -r '.model.display_name // "Unknown Model"')

used_pct=$(echo "$input" | jq -r '.context_window.used_percentage // empty')
remaining_pct=$(echo "$input" | jq -r '.context_window.remaining_percentage // empty')
ctx_size=$(echo "$input" | jq -r '.context_window.context_window_size // empty')
total_input=$(echo "$input" | jq -r '.context_window.total_input_tokens // empty')

# Build context used display
if [ -n "$used_pct" ]; then
  used_display=$(printf "%.1f%%" "$used_pct")
else
  used_display="N/A"
fi

# Build context remaining display (tokens + percentage)
if [ -n "$remaining_pct" ] && [ -n "$ctx_size" ] && [ -n "$total_input" ]; then
  remaining_tokens=$(( ctx_size - total_input ))
  remaining_display=$(printf "%.1f%% (%dk tokens)" "$remaining_pct" "$(( remaining_tokens / 1000 ))")
elif [ -n "$remaining_pct" ]; then
  remaining_display=$(printf "%.1f%%" "$remaining_pct")
else
  remaining_display="N/A"
fi

printf "%s | Used: %s | Remaining: %s" "$model" "$used_display" "$remaining_display"
