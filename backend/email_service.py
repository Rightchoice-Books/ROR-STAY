from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from typing import Optional, Dict, Any
from config import get_settings
from models import ContactSubmission, EmailNotification
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

class EmailDeliveryError(Exception):
    """Custom exception for email delivery failures"""
    pass

class EmailService:
    def __init__(self):
        if not settings.sendgrid_api_key:
            logger.warning("SendGrid API key not configured. Email functionality will be disabled.")
            self.client = None
        else:
            self.client = SendGridAPIClient(settings.sendgrid_api_key)
    
    def _is_configured(self) -> bool:
        """Check if email service is properly configured"""
        return self.client is not None and settings.sender_email is not None
    
    async def send_email(
        self, 
        to_email: str, 
        subject: str, 
        content: str, 
        content_type: str = "html"
    ) -> bool:
        """
        Send email via SendGrid
        
        Args:
            to_email: Recipient email address
            subject: Email subject line
            content: Email content (HTML or plain text)
            content_type: "html" or "plain"
        
        Returns:
            bool: True if email was sent successfully
        """
        if not self._is_configured():
            logger.error("Email service not configured. Cannot send email.")
            raise EmailDeliveryError("Email service not configured")
        
        try:
            message = Mail(
                from_email=settings.sender_email,
                to_emails=to_email,
                subject=subject,
                html_content=content if content_type == "html" else None,
                plain_text_content=content if content_type == "plain" else None
            )
            
            response = self.client.send(message)
            
            if response.status_code == 202:
                logger.info(f"Email sent successfully to {to_email}")
                return True
            else:
                logger.error(f"Failed to send email. Status code: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            raise EmailDeliveryError(f"Failed to send email: {str(e)}")
    
    async def send_contact_form_notification(self, contact_data: ContactSubmission) -> bool:
        """Send notification email for contact form submission"""
        if not self._is_configured():
            logger.warning("Email service not configured. Skipping contact form notification.")
            return False
        
        try:
            # Email to admin/support team
            admin_subject = f"New Contact Form Submission from {contact_data.name}"
            admin_content = self._generate_contact_admin_email(contact_data)
            
            # Send to admin (using sender email as recipient for now - should be configurable)
            admin_success = await self.send_email(
                to_email=settings.sender_email,
                subject=admin_subject,
                content=admin_content,
                content_type="html"
            )
            
            # Confirmation email to user
            user_subject = "Thank you for contacting ROR STAY"
            user_content = self._generate_contact_confirmation_email(contact_data)
            
            user_success = await self.send_email(
                to_email=contact_data.email,
                subject=user_subject,
                content=user_content,
                content_type="html"
            )
            
            return admin_success and user_success
            
        except Exception as e:
            logger.error(f"Failed to send contact form notification: {e}")
            return False
    
    async def send_property_inquiry_notification(
        self, 
        user_email: str, 
        user_name: str, 
        property_title: str, 
        inquiry_message: str
    ) -> bool:
        """Send notification for property inquiry"""
        if not self._is_configured():
            logger.warning("Email service not configured. Skipping property inquiry notification.")
            return False
        
        try:
            # Email to admin/agent
            admin_subject = f"New Property Inquiry: {property_title}"
            admin_content = self._generate_inquiry_admin_email(
                user_email, user_name, property_title, inquiry_message
            )
            
            admin_success = await self.send_email(
                to_email=settings.sender_email,
                subject=admin_subject,
                content=admin_content,
                content_type="html"
            )
            
            # Confirmation email to user
            user_subject = f"Your inquiry about {property_title} - ROR STAY"
            user_content = self._generate_inquiry_confirmation_email(property_title, inquiry_message)
            
            user_success = await self.send_email(
                to_email=user_email,
                subject=user_subject,
                content=user_content,
                content_type="html"
            )
            
            return admin_success and user_success
            
        except Exception as e:
            logger.error(f"Failed to send property inquiry notification: {e}")
            return False
    
    def _generate_contact_admin_email(self, contact_data: ContactSubmission) -> str:
        """Generate HTML email content for admin contact notification"""
        property_info = ""
        if contact_data.property_id:
            property_info = f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #eee;"><strong>Property ID:</strong></td>
                <td style="padding: 10px; border-bottom: 1px solid #eee;">{contact_data.property_id}</td>
            </tr>
            """
        
        phone_info = ""
        if contact_data.phone:
            phone_info = f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #eee;"><strong>Phone:</strong></td>
                <td style="padding: 10px; border-bottom: 1px solid #eee;">{contact_data.phone}</td>
            </tr>
            """
        
        return f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">
                        New Contact Form Submission
                    </h2>
                    
                    <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                        <tr>
                            <td style="padding: 10px; border-bottom: 1px solid #eee;"><strong>Name:</strong></td>
                            <td style="padding: 10px; border-bottom: 1px solid #eee;">{contact_data.name}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border-bottom: 1px solid #eee;"><strong>Email:</strong></td>
                            <td style="padding: 10px; border-bottom: 1px solid #eee;">{contact_data.email}</td>
                        </tr>
                        {phone_info}
                        {property_info}
                    </table>
                    
                    <div style="margin: 20px 0;">
                        <h3 style="color: #2c3e50;">Message:</h3>
                        <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 4px solid #3498db;">
                            {contact_data.message}
                        </div>
                    </div>
                    
                    <div style="margin-top: 30px; padding: 15px; background: #e8f4f8; border-radius: 5px;">
                        <p style="margin: 0; font-size: 14px; color: #666;">
                            <strong>Action Required:</strong> Please respond to this inquiry within 24 hours to maintain our customer service standards.
                        </p>
                    </div>
                </div>
            </body>
        </html>
        """
    
    def _generate_contact_confirmation_email(self, contact_data: ContactSubmission) -> str:
        """Generate HTML email content for user contact confirmation"""
        return f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h1 style="color: #2c3e50; margin: 0;">ROR STAY</h1>
                        <p style="color: #666; margin: 5px 0;">Real Estate Excellence</p>
                    </div>
                    
                    <h2 style="color: #2c3e50;">Thank You for Contacting Us!</h2>
                    
                    <p>Dear {contact_data.name},</p>
                    
                    <p>Thank you for reaching out to ROR STAY. We have received your message and our team will get back to you within 24 hours.</p>
                    
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h3 style="color: #2c3e50; margin-top: 0;">Your Message:</h3>
                        <p style="margin-bottom: 0;">{contact_data.message}</p>
                    </div>
                    
                    <p>In the meantime, feel free to browse our latest property listings on our website.</p>
                    
                    <div style="margin: 30px 0; padding: 20px; background: #e8f4f8; border-radius: 5px; text-align: center;">
                        <h3 style="color: #2c3e50; margin-top: 0;">Need Immediate Assistance?</h3>
                        <p style="margin: 10px 0;">Call us at: <strong>(555) 123-4567</strong></p>
                        <p style="margin: 10px 0;">Email: <strong>info@rorstay.com</strong></p>
                    </div>
                    
                    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 14px; color: #666; text-align: center;">
                        <p>Best regards,<br>The ROR STAY Team</p>
                        <p style="margin-top: 15px;">
                            This is an automated message. Please do not reply directly to this email.
                        </p>
                    </div>
                </div>
            </body>
        </html>
        """
    
    def _generate_inquiry_admin_email(
        self, 
        user_email: str, 
        user_name: str, 
        property_title: str, 
        inquiry_message: str
    ) -> str:
        """Generate HTML email content for admin property inquiry notification"""
        return f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2c3e50; border-bottom: 2px solid #e74c3c; padding-bottom: 10px;">
                        New Property Inquiry
                    </h2>
                    
                    <div style="background: #fff3cd; padding: 15px; border-radius: 5px; border: 1px solid #ffeaa7; margin: 20px 0;">
                        <h3 style="color: #856404; margin-top: 0;">Property: {property_title}</h3>
                    </div>
                    
                    <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                        <tr>
                            <td style="padding: 10px; border-bottom: 1px solid #eee;"><strong>Inquirer:</strong></td>
                            <td style="padding: 10px; border-bottom: 1px solid #eee;">{user_name}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border-bottom: 1px solid #eee;"><strong>Email:</strong></td>
                            <td style="padding: 10px; border-bottom: 1px solid #eee;">{user_email}</td>
                        </tr>
                    </table>
                    
                    <div style="margin: 20px 0;">
                        <h3 style="color: #2c3e50;">Inquiry Message:</h3>
                        <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 4px solid #e74c3c;">
                            {inquiry_message}
                        </div>
                    </div>
                    
                    <div style="margin-top: 30px; padding: 15px; background: #ffeaa7; border-radius: 5px;">
                        <p style="margin: 0; font-size: 14px; color: #856404;">
                            <strong>High Priority:</strong> Property inquiries should be responded to within 2 hours for best conversion rates.
                        </p>
                    </div>
                </div>
            </body>
        </html>
        """
    
    def _generate_inquiry_confirmation_email(self, property_title: str, inquiry_message: str) -> str:
        """Generate HTML email content for user inquiry confirmation"""
        return f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h1 style="color: #2c3e50; margin: 0;">ROR STAY</h1>
                        <p style="color: #666; margin: 5px 0;">Real Estate Excellence</p>
                    </div>
                    
                    <h2 style="color: #2c3e50;">Your Property Inquiry</h2>
                    
                    <p>Thank you for your interest in our property!</p>
                    
                    <div style="background: #e8f4f8; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #3498db;">
                        <h3 style="color: #2c3e50; margin-top: 0;">Property: {property_title}</h3>
                    </div>
                    
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h3 style="color: #2c3e50; margin-top: 0;">Your Message:</h3>
                        <p style="margin-bottom: 0;">{inquiry_message}</p>
                    </div>
                    
                    <p>Our property specialist will contact you within 2 hours during business hours to discuss this property and answer any questions you may have.</p>
                    
                    <div style="margin: 30px 0; padding: 20px; background: #d4edda; border-radius: 5px; border: 1px solid #c3e6cb;">
                        <h3 style="color: #155724; margin-top: 0;">What's Next?</h3>
                        <ul style="color: #155724; margin: 0; padding-left: 20px;">
                            <li>We'll review your inquiry and property details</li>
                            <li>A specialist will call or email you soon</li>
                            <li>We can schedule a viewing at your convenience</li>
                            <li>Get answers to all your questions about the property</li>
                        </ul>
                    </div>
                    
                    <div style="margin: 30px 0; padding: 20px; background: #e8f4f8; border-radius: 5px; text-align: center;">
                        <h3 style="color: #2c3e50; margin-top: 0;">Need Immediate Assistance?</h3>
                        <p style="margin: 10px 0;">Call us at: <strong>(555) 123-4567</strong></p>
                        <p style="margin: 10px 0;">Email: <strong>info@rorstay.com</strong></p>
                    </div>
                    
                    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 14px; color: #666; text-align: center;">
                        <p>Best regards,<br>The ROR STAY Team</p>
                        <p style="margin-top: 15px;">
                            This is an automated message. Please do not reply directly to this email.
                        </p>
                    </div>
                </div>
            </body>
        </html>
        """

# Create a singleton instance
email_service = EmailService()

# Dependency for FastAPI
def get_email_service() -> EmailService:
    return email_service