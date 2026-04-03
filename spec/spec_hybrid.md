# Requirement ID: FR_hybrid_1
- Description: [The app should show the full subscription price, billing period, renewal terms, and any trial terms before the user confirms payment.]
- Source Persona: [Subscription Concerned Subscriber]
- Traceability: [Derived from persona AP1 in personas_hybrid.json, which was refined from review group A1 in review_groups_hybrid.json]
- Acceptance Criteria: [Given a user is about to start a trial or paid plan, when the payment screen appears, then it must show the exact price, billing period, trial length if there is one, and whether the plan renews automatically before payment is confirmed.]

# Requirement ID: FR_hybrid_2
- Description: [The app should have a subscription status screen that shows whether the user is on a trial or a paid plan, the next billing date, the billing source, and how to cancel.]
- Source Persona: [Subscription Concerned Subscriber]
- Traceability: [Derived from persona AP1 in personas_hybrid.json, which was refined from review group A1 in review_groups_hybrid.json]
- Acceptance Criteria: [Given a user with a trial or paid plan opens account settings, when the subscription section loads, then it must show the current plan state, the next billing date, the billing source, and the cancellation method.]

# Requirement ID: FR_hybrid_3
- Description: [The app should confirm a successful cancellation in the same flow and keep the canceled status visible in the user account.]
- Source Persona: [Subscription Concerned Subscriber]
- Traceability: [Derived from persona AP1 in personas_hybrid.json, which was refined from review group A1 in review_groups_hybrid.json]
- Acceptance Criteria: [Given a user cancels a trial or subscription, when the cancellation finishes, then the app must show a confirmation message and keep the canceled status visible the next time the user opens the account screen.]

# Requirement ID: FR_hybrid_4
- Description: [The app should route billing help based on the payment provider so the user sees the correct refund or payment instructions.]
- Source Persona: [Subscription Concerned Subscriber]
- Traceability: [Derived from persona AP1 in personas_hybrid.json, which was refined from review group A1 in review_groups_hybrid.json]
- Acceptance Criteria: [Given a user opens billing help for a payment problem, when the help flow loads, then it must identify the billing source and show the matching refund or payment support path.]

# Requirement ID: FR_hybrid_5
- Description: [The app should open to the main home screen on supported devices without crashing.]
- Source Persona: [Reliability Focused Daily User]
- Traceability: [Derived from persona AP2 in personas_hybrid.json, which was refined from review group A2 in review_groups_hybrid.json]
- Acceptance Criteria: [Given the app is installed on a supported device, when the user opens it from the device launcher, then the home screen must load without crashing or freezing.]

# Requirement ID: FR_hybrid_6
- Description: [The app should let users move between core screens, including home, sleep, and meditation content, without freezing or forcing a restart.]
- Source Persona: [Reliability Focused Daily User]
- Traceability: [Derived from persona AP2 in personas_hybrid.json, which was refined from review group A2 in review_groups_hybrid.json]
- Acceptance Criteria: [Given a user moves between core screens in one session, when each screen opens, then the app must stay responsive and let the user continue without needing to force close the app.]

# Requirement ID: FR_hybrid_7
- Description: [The app should show an error state with a retry action when content does not load.]
- Source Persona: [Reliability Focused Daily User]
- Traceability: [Derived from persona AP2 in personas_hybrid.json, which was refined from review group A2 in review_groups_hybrid.json]
- Acceptance Criteria: [Given a content screen cannot load, when the failure is detected, then the app must show an error message with a retry action instead of leaving the user on a blank, frozen, or broken screen.]

# Requirement ID: FR_hybrid_8
- Description: [The app should keep meditation audio playing until the session ends unless the user pauses or stops it.]
- Source Persona: [Interrupted Meditation Listener]
- Traceability: [Derived from persona AP3 in personas_hybrid.json, which was refined from review group A3 in review_groups_hybrid.json]
- Acceptance Criteria: [Given a user starts a meditation session and the required connection is available or the content was downloaded, when the session is playing, then the audio must continue until the session ends unless the user pauses or stops it.]

# Requirement ID: FR_hybrid_9
- Description: [The app should show playback failures in the same meditation session and offer a resume action from the last played point.]
- Source Persona: [Interrupted Meditation Listener]
- Traceability: [Derived from persona AP3 in personas_hybrid.json, which was refined from review group A3 in review_groups_hybrid.json]
- Acceptance Criteria: [Given playback is interrupted by an error, when the interruption happens, then the app must show the failure in that same session and offer a resume action that restarts from the last played point.]

# Requirement ID: FR_hybrid_10
- Description: [The app should play downloaded meditation content when the device is offline.]
- Source Persona: [Interrupted Meditation Listener]
- Traceability: [Derived from persona AP3 in personas_hybrid.json, which was refined from review group A3 in review_groups_hybrid.json]
- Acceptance Criteria: [Given a user has downloaded a meditation session, when the device is offline and the user starts it, then the session must play without showing a false offline or buffering error.]

# Requirement ID: FR_hybrid_11
- Description: [The app should keep Sleepcasts, soundscapes, and other bedtime audio playing when the screen is off on supported devices.]
- Source Persona: [Bedtime Sleep Audio User]
- Traceability: [Derived from persona AP4 in personas_hybrid.json, which was refined from review group A4 in review_groups_hybrid.json]
- Acceptance Criteria: [Given a user starts sleep audio and turns off the screen, when the device enters a supported idle state, then the audio must keep playing until the content ends or the user stops it.]

# Requirement ID: FR_hybrid_12
- Description: [The app should avoid unexpected vibration or blocking prompts after sleep audio starts unless the user enabled that feedback.]
- Source Persona: [Bedtime Sleep Audio User]
- Traceability: [Derived from persona AP4 in personas_hybrid.json, which was refined from review group A4 in review_groups_hybrid.json]
- Acceptance Criteria: [Given a user has already started sleep audio, when the user returns to the sleep section during that session, then the app must not trigger vibration or a blocking prompt unless that feedback was enabled in settings.]

# Requirement ID: FR_hybrid_13
- Description: [The app should let users browse sleep content by content type and sound theme.]
- Source Persona: [Bedtime Sleep Audio User]
- Traceability: [Derived from persona AP4 in personas_hybrid.json, which was refined from review group A4 in review_groups_hybrid.json]
- Acceptance Criteria: [Given a user is browsing sleep content, when the user opens the available filter or category controls, then the app must let the user narrow the list by content type or sound theme and update the results.]

# Requirement ID: FR_hybrid_14
- Description: [The app should organize guided content by common needs, including stress, sleep, grief, and daily practice.]
- Source Persona: [Routine Building Mindfulness User]
- Traceability: [Derived from persona AP5 in personas_hybrid.json, which was refined from review group A5 in review_groups_hybrid.json]
- Acceptance Criteria: [Given a user is looking for support for a specific need, when the user browses or searches the library, then the app must show categories or entry points for stress, sleep, grief, and daily practice.]

# Requirement ID: FR_hybrid_15
- Description: [The app should track completed sessions and show session history or milestones so users can follow their routine over time.]
- Source Persona: [Routine Building Mindfulness User]
- Traceability: [Derived from persona AP5 in personas_hybrid.json, which was refined from review group A5 in review_groups_hybrid.json]
- Acceptance Criteria: [Given a user completes sessions over multiple days, when the user checks progress, then the app must show session history or milestone progress that matches those completed sessions.]
