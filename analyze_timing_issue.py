#!/usr/bin/env python3
"""
Analyze why AI classification might take 500+ seconds
"""

print("=== Analyzing AI Classification Timing ===\n")

print("The code enforces a MINIMUM 70-second delay for AI classification.")
print("But if the actual API call takes longer, it uses the real time.\n")

print("Possible reasons for 500+ second timing:")
print("1. Azure OpenAI API is actually slow/throttled")
print("2. Network latency to Azure")
print("3. Large document causing multiple API calls")
print("4. API timeout/retry logic adding delays")
print("5. Rate limiting on the API")

print("\nFrom the orchestrator code:")
print("- Minimum enforced delay: 70 seconds")
print("- API timeout setting: 60 seconds")
print("- If API takes 500s, that's the actual API response time")

print("\nTo debug:")
print("1. Check Azure OpenAI logs for latency")
print("2. Monitor API response times")
print("3. Check if document size affects timing")
print("4. Look for rate limit errors in logs")

# Calculate what the timings mean
total_time = 82.13  # What metadata shows
ai_time = 500  # What you're seeing

print(f"\nTiming Analysis:")
print(f"- Metadata shows total: {total_time}s")
print(f"- You report AI step: {ai_time}s")
print(f"- This suggests metadata might be from a different run")
print(f"- Or the logging is showing different timing than actual")

print("\nThe 70s in the code is a MINIMUM, not the actual time.")
print("If Azure OpenAI is slow, it will take the real time (500s in your case).")