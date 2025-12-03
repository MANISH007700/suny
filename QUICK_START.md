# 🚀 Quick Start - Advisor Dashboard

## Start in 3 Steps

### Step 1: Start Backend
```bash
cd backend
python main.py
```
✅ Backend should be running on http://localhost:8888

### Step 2: Start Frontend
```bash
cd frontend
streamlit run app.py
```
✅ Frontend opens automatically at http://localhost:8501

### Step 3: Access Advisor Dashboard
1. Look at the **sidebar** on the left
2. Under "👤 User Mode", select **"👨‍🏫 Advisor"**
3. Click the **"🎯 Advisor Dashboard"** tab at the top
4. You'll see 5 pre-loaded sample escalations!

## What You'll See

### Dashboard Stats (Top Row)
- **Total Escalations**: 5
- **Pending**: 3
- **In Progress**: 1
- **Resolved**: 1
- **High Risk Students**: 2

### Sample Escalations

Click on any escalation to expand it. Try these:

**🔴 HIGH PRIORITY** - Marcus Thompson (Failing Courses)
- Status: In Progress
- Priority: ⭐⭐⭐⭐⭐
- Already has advisor notes
- Critical risk student

**🔴 URGENT** - Emily Rodriguez (Financial Aid)
- Status: Pending
- Priority: ⭐⭐⭐⭐
- High risk student
- Needs immediate attention

**🟢 RESOLVED** - Sophia Chen (Waiver Request)
- Status: Resolved
- Priority: ⭐⭐
- Example of completed escalation
- See how notes document the resolution

## Test the Features

### Try This: Update an Escalation

1. Click on **Emily Rodriguez's financial aid escalation**
2. Change status from "pending" to "in_progress"
3. In the note field, type:
   ```
   Scheduled meeting with Financial Aid Office. Following up on scholarship denial.
   ```
4. In "Assign To", type your name (e.g., "Dr. Sarah Johnson")
5. Click **"💾 Update Escalation"**
6. Watch it save and refresh!

### Try This: Generate an Automatic Escalation

1. Switch to **"🎓 Student"** mode in sidebar
2. Make sure Student ID shows "STUDENT_001"
3. Go to **"💬 Academic Guidance Chat"** tab
4. Ask: "I need emergency financial help, I can't pay tuition"
5. Watch for the escalation notification!
6. Switch back to **"👨‍🏫 Advisor"** mode
7. Refresh the dashboard - you'll see your new escalation!

### Try This: Manual Escalation (NEW!)

1. In **"🎓 Student"** mode, ask any question
2. Wait for AI response
3. Click **"🆘 Escalate to Advisor"** button
4. Fill out the form:
   - Your question (pre-filled)
   - AI response (pre-filled)
   - Select reason: "Need personalized academic guidance"
   - Set urgency: ⭐⭐⭐ Medium
   - Add notes: "Need help planning my course schedule"
5. Click **"✅ Submit to Advisor"**
6. See confirmation with escalation ID!
7. Switch to Advisor mode to see it in queue

## Understanding the Interface

### Left Column (Main Content)
- 💬 Student Question (blue/teal highlight)
- 🤖 AI Response (dark background)
- 📝 Escalation Reason (yellow warning)
- 💬 Conversation History (expandable)
- 📌 Advisor Notes (if any exist)

### Right Column (Student Profile)
- 👤 Name, Major, GPA
- Risk Level (color-coded: green/yellow/orange/red)
- Total escalations count
- Completed & current courses
- Last interaction date

### Bottom Section (Actions)
- Update Status dropdown
- Priority selector (1-5)
- Add Note text area
- Assign To field
- Update button

### Bottom of Page
- 🚨 "Students Needing Attention" section
- Shows repeat students
- Quick access to their profiles

## Filtering Options

Try these filter combinations:

**Show only pending items:**
- Filter by Status: "pending"

**Show high-priority only:**
- Min Priority: 4 or 5

**Show all resolved:**
- Filter by Status: "resolved"

## Color Coding

### Risk Levels
- 🟢 **Green** = Low risk (0-2 escalations, good standing)
- 🟡 **Yellow** = Medium risk (3-4 escalations)
- 🟠 **Orange** = High risk (5+ escalations)
- 🔴 **Red** = Critical risk (failing + multiple escalations)

### Status
- **Pending** = Needs attention
- **In Progress** = Currently being handled
- **Resolved** = Issue addressed
- **Closed** = Archived

### Priority Stars
- ⭐ = Low priority
- ⭐⭐ = Normal
- ⭐⭐⭐ = Medium
- ⭐⭐⭐⭐ = High
- ⭐⭐⭐⭐⭐ = Critical/Urgent

## Common Questions

**Q: How do I switch between student and advisor mode?**
A: Use the radio buttons in the sidebar under "👤 User Mode"

**Q: How are escalations created?**
A: Automatically when students ask about sensitive topics (financial aid, failing, withdrawal, accommodations, etc.)

**Q: Can I create escalations manually?**
A: Yes! Use the POST /advisor/escalations endpoint or add the feature to the UI

**Q: Where is the data stored?**
A: In JSON files: `backend/data/escalations.json` and `backend/data/student_profiles.json`

**Q: Can I delete test escalations?**
A: Yes, but only via API currently. Use DELETE /advisor/escalations/{id}

**Q: How do I see which students need help most?**
A: Check the "Students Needing Attention" section at the bottom of the dashboard

## Pro Tips

1. **Check dashboard twice daily** for new pending escalations
2. **Update status immediately** when you start working on something
3. **Add detailed notes** so other advisors can follow along
4. **Use priority levels** to organize your workload
5. **Assign to specialists** for issues outside your expertise
6. **Watch for repeat students** - they may need proactive outreach

## Sample Workflow

```
1. See new pending escalation (⚠️ notification)
2. Click to expand and read details
3. Review student profile (right column)
4. Check conversation history
5. Change status to "in progress"
6. Add note: "Contacting Financial Aid Office"
7. Assign to: "Financial Aid Advisor"
8. Click Update
9. Follow up with student
10. Add resolution note
11. Change status to "resolved"
```

## Troubleshooting

**Dashboard not showing?**
- Make sure you're in "👨‍🏫 Advisor" mode
- Check that backend is running (http://localhost:8888/health)

**No escalations showing?**
- Sample data is in `backend/data/escalations.json`
- Check file exists and has content
- Try refreshing the page

**Can't update escalations?**
- Check browser console for errors
- Verify backend is running
- Check API logs for error messages

**Changes not saving?**
- Make sure you clicked "💾 Update Escalation"
- Check that at least one field changed
- Refresh the page after update

## Need Help?

- Full guide: See `ADVISOR_DASHBOARD_GUIDE.md`
- Technical details: See `IMPLEMENTATION_SUMMARY.md`
- API docs: http://localhost:8888/docs

---

**You're all set! Start exploring the Advisor Dashboard! 🎉**

