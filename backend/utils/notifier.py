import os
import resend
from dotenv import load_dotenv

load_dotenv()

resend.api_key = os.getenv("RESEND_API_KEY")

def send_payment_success_email(user_email, baby_name):
    """Sends an email confirming payment and that the song is queued."""
    if not user_email or not resend.api_key:
        return False
    
    try:
        html_content = f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #eee; border-radius: 10px;">
            <h2 style="color: #644d3a;">🎶 We've started! Your song for {baby_name} is in the works.</h2>
            <p>Hello,</p>
            <p>We've successfully queued your personalized song for <strong>{baby_name}</strong>.</p>
            
            <p>Our magical nursery is now:</p>
            <ul style="color: #666; line-height: 1.6;">
                <li>✍️ Writing unique lyrics</li>
                <li>🎨 Painting custom artwork</li>
                <li>🎵 Generating vocals & music</li>
                <li>📽️ Assembling your high-quality video</li>
                <li>📺 Uploading to YouTube (if selected)</li>
            </ul>

            <p>This process usually takes about <strong>10-15 minutes</strong>. We will send you another email as soon as it's ready!</p>
            
            <hr style="border: 0; border-top: 1px solid #eee; margin: 30px 0;">
            <p style="font-size: 0.9rem; color: #666;">Warmly,<br>The Mithi Baby Team</p>
        </div>
        """
        
        params = {
            "from": "Mithi Baby <hello@mithi.baby>",
            "to": [user_email],
            "subject": f"🎶 We've started on {baby_name}'s song!",
            "html": html_content,
        }
        
        resend.Emails.send(params)
        return True
    except Exception as e:
        print(f"❌ Failed to send success email: {e}")
        return False

def send_completion_email(user_email, baby_name, song_title, video_url, youtube_url=None):
    """Sends a notification email when the song is ready."""
    if not user_email or not resend.api_key:
        print(f"⚠️ Skipping email: email={user_email}, api_key_set={bool(resend.api_key)}")
        return False

    try:
        yt_section = ""
        if youtube_url:
            yt_section = f"""
            <div style="text-align: center; margin: 15px 0;">
                <a href="{youtube_url}" style="background-color: #ff0000; color: white; padding: 12px 25px; text-decoration: none; border-radius: 25px; font-weight: bold;">View on YouTube 📺</a>
            </div>
            """

        html_content = f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #eee; border-radius: 10px;">
            <h2 style="color: #644d3a;">✨ Your Magical Song for {baby_name} is Ready!</h2>
            <p>Hello,</p>
            <p>We are thrilled to let you know that <strong>"{song_title}"</strong> has been created just for your little one.</p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{video_url}" style="background-color: #a6968a; color: white; padding: 12px 25px; text-decoration: none; border-radius: 25px; font-weight: bold;">Watch Your Video</a>
            </div>

            {yt_section}
            
            <p>You can also find it in your library on Mithi.baby anytime.</p>
            <p>Thank you for choosing Mithi Baby to celebrate your heritage!</p>
            
            <hr style="border: 0; border-top: 1px solid #eee; margin: 30px 0;">
            <p style="font-size: 0.9rem; color: #666;">With love,<br>The Mithi Baby Team</p>
        </div>
        """

        params = {
            "from": "Mithi Baby <hello@mithi.baby>",
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
