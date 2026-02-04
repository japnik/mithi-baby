import os
import resend
from dotenv import load_dotenv

load_dotenv()

resend.api_key = os.getenv("RESEND_API_KEY")

def send_completion_email(user_email, baby_name, song_title, video_url):
    """Sends a notification email when the song is ready."""
    if not user_email or not resend.api_key:
        print(f"⚠️ Skipping email: email={user_email}, api_key_set={bool(resend.api_key)}")
        return False

    try:
        html_content = f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #eee; border-radius: 10px;">
            <h2 style="color: #644d3a;">✨ Your Magical Song for {baby_name} is Ready!</h2>
            <p>Hello,</p>
            <p>We are thrilled to let you know that <strong>"{song_title}"</strong> has been created just for your little one.</p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{video_url}" style="background-color: #a6968a; color: white; padding: 12px 25px; text-decoration: none; border-radius: 25px; font-weight: bold;">Watch Your Video</a>
            </div>
            
            <p>You can also find it in your library on Mithi.baby anytime.</p>
            
            <hr style="border: 0; border-top: 1px solid #eee; margin: 30px 0;">
            <p style="font-size: 0.9rem; color: #666;">With love,<br>The Mithi Baby Team</p>
        </div>
        """

        params = {
            "from": "Mithi Baby <onboarding@resend.dev>", # Note: Resend requires a verified domain or this default for testing
            "to": [user_email],
            "subject": f"✨ {baby_name}'s Magical Song is Ready!",
            "html": html_content,
        }

        email = resend.Emails.send(params)
        print(f"✅ Email sent successfully to {user_email}. ID: {email['id']}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False
