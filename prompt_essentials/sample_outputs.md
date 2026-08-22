# Sample Outputs for Prompt Essentials

These are representative outputs for trainers to use when the classroom API key is unavailable or rate-limited. The notebook has built-in simulated outputs, so it can still run end-to-end without live API access.

## Bad summary prompt

The customer is unhappy because the laptop is late and support has not resolved the issue.

## Improved summary prompt

Issue: Delayed laptop delivery and repeated support failures.  
Customer impact: Cannot start a work project on time.  
Urgency: High.  
Recommended action: Escalate to logistics support, provide a delivery ETA, and offer a callback.

## Few-shot ticket router

```json
{
  "category": "Billing",
  "priority": "High",
  "reason": "The ticket combines duplicate payment with business impact and repeated failed support attempts."
}
```

## Strong system message for travel assistant

```json
{
  "can_answer": false,
  "missing_information": ["departure city", "travel dates", "budget", "traveller count"],
  "safe_next_question": "Which city are you departing from, what dates are you considering, and what budget should I work within?",
  "assumptions_made": []
}
```

## Debugged travel prompt

```json
{
  "answer_status": "needs_clarification",
  "risk_flags": ["weather may be seasonal", "budget not specified", "departure city missing"],
  "clarifying_questions": ["Which city are you flying from?", "What is your budget range?", "Are your dates flexible?"],
  "safe_response": "I can help shortlist beach options, but I should not invent live weather or flight prices without a source."
}
```
