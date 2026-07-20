import nodemailer from 'nodemailer';
import dotenv from 'dotenv';

dotenv.config();

class EmailService {
  constructor() {
    this.transporter = null;
    this.initializeTransporter();
  }

  initializeTransporter() {
    // Check if SMTP credentials are configured
    if (!process.env.SMTP_USER || !process.env.SMTP_PASSWORD) {
      console.warn('⚠️ Email service not configured. Set SMTP credentials in .env file');
      return;
    }

    this.transporter = nodemailer.createTransport({
      host: process.env.SMTP_HOST || 'smtp.gmail.com',
      port: parseInt(process.env.SMTP_PORT) || 587,
      secure: process.env.SMTP_SECURE === 'true',
      auth: {
        user: process.env.SMTP_USER,
        pass: process.env.SMTP_PASSWORD
      }
    });

    // Verify connection
    this.transporter.verify((error, success) => {
      if (error) {
        console.error('❌ Email service error:', error.message);
      } else {
        console.log('✅ Email service ready');
      }
    });
  }

  async sendRestockEmail(product, restockRequest) {
    if (!this.transporter) {
      console.log('📧 Email service not configured. Would have sent restock email for:', product.name);
      return { success: false, message: 'Email service not configured' };
    }

    try {
      const mailOptions = {
        from: {
          name: process.env.SMTP_FROM_NAME || 'AI CRM Logistics',
          address: process.env.SMTP_FROM_EMAIL || process.env.SMTP_USER
        },
        to: restockRequest.supplierEmail,
        subject: `🔔 Urgent: Restock Request for ${product.name}`,
        html: this.getRestockEmailTemplate(product, restockRequest)
      };

      const info = await this.transporter.sendMail(mailOptions);
      console.log('✅ Restock email sent:', info.messageId);
      
      return { success: true, messageId: info.messageId };
    } catch (error) {
      console.error('❌ Email sending failed:', error.message);
      return { success: false, message: error.message };
    }
  }

  getRestockEmailTemplate(product, restockRequest) {
    return `
      <!DOCTYPE html>
      <html>
      <head>
        <style>
          body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
          .container { max-width: 600px; margin: 0 auto; padding: 20px; }
          .header { background: #10b981; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }
          .content { background: #f9fafb; padding: 30px; border: 1px solid #e5e7eb; }
          .product-details { background: white; padding: 20px; border-radius: 8px; margin: 20px 0; }
          .detail-row { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #e5e7eb; }
          .detail-label { font-weight: bold; color: #6b7280; }
          .detail-value { color: #111827; }
          .urgent { color: #dc2626; font-weight: bold; }
          .footer { background: #1f2937; color: #9ca3af; padding: 20px; text-align: center; border-radius: 0 0 8px 8px; font-size: 14px; }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="header">
            <h1>🔔 Restock Request</h1>
          </div>
          
          <div class="content">
            <p>Dear Supplier,</p>
            
            <p>This is an automated notification from our AI CRM Logistics System.</p>
            
            <p class="urgent">⚠️ URGENT: Stock level has fallen below minimum threshold</p>
            
            <div class="product-details">
              <h3 style="margin-top: 0; color: #10b981;">Product Information</h3>
              
              <div class="detail-row">
                <span class="detail-label">Product Name:</span>
                <span class="detail-value">${product.name}</span>
              </div>
              
              <div class="detail-row">
                <span class="detail-label">SKU:</span>
                <span class="detail-value">${product.sku}</span>
              </div>
              
              <div class="detail-row">
                <span class="detail-label">Current Stock:</span>
                <span class="detail-value urgent">${restockRequest.currentStock} ${product.unit}</span>
              </div>
              
              <div class="detail-row">
                <span class="detail-label">Minimum Threshold:</span>
                <span class="detail-value">${restockRequest.threshold} ${product.unit}</span>
              </div>
              
              <div class="detail-row">
                <span class="detail-label">Requested Quantity:</span>
                <span class="detail-value"><strong>${restockRequest.requestedQuantity} ${product.unit}</strong></span>
              </div>
              
              <div class="detail-row" style="border-bottom: none;">
                <span class="detail-label">Request Date:</span>
                <span class="detail-value">${new Date().toLocaleString()}</span>
              </div>
            </div>
            
            <p><strong>Action Required:</strong></p>
            <p>Please arrange to supply the requested quantity at your earliest convenience.</p>
            
            <p>For any questions or to confirm delivery, please contact our admin team.</p>
          </div>
          
          <div class="footer">
            <p><strong>AI CRM Logistics System</strong></p>
            <p>This is an automated message. Please do not reply directly to this email.</p>
            <p style="margin-top: 10px; font-size: 12px;">
              © ${new Date().getFullYear()} AI CRM Logistics. All rights reserved.
            </p>
          </div>
        </div>
      </body>
      </html>
    `;
  }

  async sendOrderConfirmation(order, customer) {
    if (!this.transporter) {
      console.log('📧 Email service not configured. Would have sent order confirmation');
      return { success: false, message: 'Email service not configured' };
    }

    try {
      const mailOptions = {
        from: {
          name: process.env.SMTP_FROM_NAME || 'AI CRM Logistics',
          address: process.env.SMTP_FROM_EMAIL || process.env.SMTP_USER
        },
        to: customer.email,
        subject: `Order Confirmation - ${order.orderNumber}`,
        html: this.getOrderConfirmationTemplate(order, customer)
      };

      const info = await this.transporter.sendMail(mailOptions);
      console.log('✅ Order confirmation email sent:', info.messageId);
      
      return { success: true, messageId: info.messageId };
    } catch (error) {
      console.error('❌ Email sending failed:', error.message);
      return { success: false, message: error.message };
    }
  }

  async sendOrderDispatched(order, customer) {
    if (!this.transporter) {
      console.log('📧 Email service not configured. Would have sent order dispatched email');
      return { success: false, message: 'Email service not configured' };
    }

    try {
      const mailOptions = {
        from: {
          name: process.env.SMTP_FROM_NAME || 'AI CRM Logistics',
          address: process.env.SMTP_FROM_EMAIL || process.env.SMTP_USER,
        },
        to: customer.email,
        subject: `Order Dispatched - ${order.orderNumber}`,
        html: this.getOrderStatusTemplate(order, customer, 'DISPATCHED'),
      };

      const info = await this.transporter.sendMail(mailOptions);
      console.log('✅ Order dispatched email sent:', info.messageId);
      return { success: true, messageId: info.messageId };
    } catch (error) {
      console.error('❌ Email sending failed:', error.message);
      return { success: false, message: error.message };
    }
  }

  async sendOrderDelivered(order, customer) {
    if (!this.transporter) {
      console.log('📧 Email service not configured. Would have sent order delivered email');
      return { success: false, message: 'Email service not configured' };
    }

    try {
      const mailOptions = {
        from: {
          name: process.env.SMTP_FROM_NAME || 'AI CRM Logistics',
          address: process.env.SMTP_FROM_EMAIL || process.env.SMTP_USER,
        },
        to: customer.email,
        subject: `Order Delivered - ${order.orderNumber}`,
        html: this.getOrderStatusTemplate(order, customer, 'DELIVERED'),
      };

      const info = await this.transporter.sendMail(mailOptions);
      console.log('✅ Order delivered email sent:', info.messageId);
      return { success: true, messageId: info.messageId };
    } catch (error) {
      console.error('❌ Email sending failed:', error.message);
      return { success: false, message: error.message };
    }
  }

  getOrderStatusTemplate(order, customer, status) {
    const statusTitle = status === 'DISPATCHED' ? '🚚 Order Dispatched' : '✅ Order Delivered';
    const statusMessage = status === 'DISPATCHED'
      ? 'Your order has been dispatched and is on the way.'
      : 'Your order has been marked as delivered. Thank you for confirming receipt.';
    const timestamp = status === 'DISPATCHED'
      ? order.tracking?.dispatchedAt
      : order.tracking?.deliveredAt;

    return `
      <!DOCTYPE html>
      <html>
      <head>
        <style>
          body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
          .container { max-width: 600px; margin: 0 auto; padding: 20px; }
          .header { background: #3b82f6; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }
          .content { background: #f9fafb; padding: 30px; border: 1px solid #e5e7eb; }
          .details { background: white; padding: 20px; border-radius: 8px; margin: 20px 0; }
          .detail-row { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #e5e7eb; }
          .detail-label { font-weight: bold; color: #6b7280; }
          .detail-value { color: #111827; }
          .footer { background: #1f2937; color: #9ca3af; padding: 20px; text-align: center; border-radius: 0 0 8px 8px; font-size: 14px; }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="header">
            <h1>${statusTitle}</h1>
          </div>
          <div class="content">
            <p>Dear ${customer.name},</p>
            <p>${statusMessage}</p>
            <div class="details">
              <h3 style="margin-top: 0; color: #3b82f6;">Order Status Update</h3>
              <div class="detail-row">
                <span class="detail-label">Order Number:</span>
                <span class="detail-value"><strong>${order.orderNumber}</strong></span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Status:</span>
                <span class="detail-value"><strong>${status}</strong></span>
              </div>
              <div class="detail-row" style="border-bottom: none;">
                <span class="detail-label">Updated At:</span>
                <span class="detail-value">${timestamp ? new Date(timestamp).toLocaleString() : new Date().toLocaleString()}</span>
              </div>
            </div>
            <p>You can track your order status from your dashboard.</p>
          </div>
          <div class="footer">
            <p><strong>AI CRM Logistics System</strong></p>
            <p>© ${new Date().getFullYear()} AI CRM Logistics. All rights reserved.</p>
          </div>
        </div>
      </body>
      </html>
    `;
  }

  getOrderConfirmationTemplate(order, customer) {
    const itemsHtml = order.items.map(item => `
      <div class="detail-row">
        <span class="detail-label">${item.productName} (${item.sku})</span>
        <span class="detail-value">${item.quantity} × ₹${item.price} = ₹${item.total}</span>
      </div>
    `).join('');

    return `
      <!DOCTYPE html>
      <html>
      <head>
        <style>
          body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
          .container { max-width: 600px; margin: 0 auto; padding: 20px; }
          .header { background: #3b82f6; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }
          .content { background: #f9fafb; padding: 30px; border: 1px solid #e5e7eb; }
          .product-details { background: white; padding: 20px; border-radius: 8px; margin: 20px 0; }
          .detail-row { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #e5e7eb; }
          .detail-label { font-weight: bold; color: #6b7280; }
          .detail-value { color: #111827; }
          .total { font-size: 18px; font-weight: bold; color: #10b981; }
          .footer { background: #1f2937; color: #9ca3af; padding: 20px; text-align: center; border-radius: 0 0 8px 8px; font-size: 14px; }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="header">
            <h1>✅ Order Confirmed</h1>
          </div>
          
          <div class="content">
            <p>Dear ${customer.name},</p>
            
            <p>Thank you for your order! We have received it and will process it shortly.</p>
            
            <div class="product-details">
              <h3 style="margin-top: 0; color: #3b82f6;">Order Details</h3>
              
              <div class="detail-row">
                <span class="detail-label">Order Number:</span>
                <span class="detail-value"><strong>${order.orderNumber}</strong></span>
              </div>
              
              <div class="detail-row">
                <span class="detail-label">Order Date:</span>
                <span class="detail-value">${new Date(order.tracking.placedAt).toLocaleString()}</span>
              </div>
              
              <div style="margin-top: 20px;">
                <h4 style="color: #6b7280;">Items:</h4>
                ${itemsHtml}
              </div>
              
              <div class="detail-row" style="border-bottom: none; margin-top: 20px;">
                <span class="detail-label total">Total Amount:</span>
                <span class="detail-value total">₹${order.totalAmount}</span>
              </div>
            </div>
            
            <p>You can track your order status from your dashboard.</p>
          </div>
          
          <div class="footer">
            <p><strong>AI CRM Logistics System</strong></p>
            <p>© ${new Date().getFullYear()} AI CRM Logistics. All rights reserved.</p>
          </div>
        </div>
      </body>
      </html>
    `;
  }

  // Send custom email to supplier
  async sendSupplierEmail({ to, supplierName, subject, message, emailType = 'general' }) {
    if (!this.transporter) {
      console.log('📧 Email service not configured. Would have sent supplier email');
      return { success: false, message: 'Email service not configured' };
    }

    try {
      const mailOptions = {
        from: {
          name: process.env.SMTP_FROM_NAME || 'AI CRM Logistics',
          address: process.env.SMTP_FROM_EMAIL || process.env.SMTP_USER
        },
        to: to,
        subject: subject,
        html: this.getSupplierEmailTemplate(supplierName, subject, message, emailType)
      };

      const info = await this.transporter.sendMail(mailOptions);
      console.log('✅ Supplier email sent:', info.messageId);
      
      return { success: true, messageId: info.messageId };
    } catch (error) {
      console.error('❌ Supplier email sending failed:', error.message);
      return { success: false, message: error.message };
    }
  }

  // Send purchase order to supplier
  async sendPurchaseOrderEmail({ supplierEmail, supplierName, items, orderNumber, deliveryDate }) {
    if (!this.transporter) {
      console.log('📧 Email service not configured. Would have sent purchase order');
      return { success: false, message: 'Email service not configured' };
    }

    try {
      const mailOptions = {
        from: {
          name: process.env.SMTP_FROM_NAME || 'AI CRM Logistics',
          address: process.env.SMTP_FROM_EMAIL || process.env.SMTP_USER
        },
        to: supplierEmail,
        subject: `Purchase Order #${orderNumber}`,
        html: this.getPurchaseOrderTemplate(supplierName, items, orderNumber, deliveryDate)
      };

      const info = await this.transporter.sendMail(mailOptions);
      console.log('✅ Purchase order email sent:', info.messageId);
      
      return { success: true, messageId: info.messageId };
    } catch (error) {
      console.error('❌ Purchase order email failed:', error.message);
      return { success: false, message: error.message };
    }
  }

  // Send shipment notification
  async sendShipmentNotification({ to, trackingNumber, estimatedDelivery }) {
    if (!this.transporter) {
      console.log('📧 Email service not configured. Would have sent shipment notification');
      return { success: false, message: 'Email service not configured' };
    }

    try {
      const mailOptions = {
        from: {
          name: process.env.SMTP_FROM_NAME || 'AI CRM Logistics',
          address: process.env.SMTP_FROM_EMAIL || process.env.SMTP_USER
        },
        to: to,
        subject: '📦 Your Order Has Been Shipped',
        html: this.getShipmentTemplate(trackingNumber, estimatedDelivery)
      };

      const info = await this.transporter.sendMail(mailOptions);
      console.log('✅ Shipment notification sent:', info.messageId);
      
      return { success: true, messageId: info.messageId };
    } catch (error) {
      console.error('❌ Shipment notification failed:', error.message);
      return { success: false, message: error.message };
    }
  }

  getSupplierEmailTemplate(supplierName, subject, message, emailType) {
    const icon = emailType === 'urgent' ? '🚨' : emailType === 'restock' ? '📦' : '📧';
    
    return `
      <!DOCTYPE html>
      <html>
      <head>
        <style>
          body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
          .container { max-width: 600px; margin: 0 auto; padding: 20px; }
          .header { background: #10b981; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }
          .content { background: #f9fafb; padding: 30px; border: 1px solid #e5e7eb; }
          .message-box { background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #10b981; }
          .footer { background: #1f2937; color: #9ca3af; padding: 20px; text-align: center; border-radius: 0 0 8px 8px; font-size: 14px; }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="header">
            <h1>${icon} ${subject}</h1>
          </div>
          
          <div class="content">
            <p>Dear ${supplierName},</p>
            
            <div class="message-box">
              <p style="margin: 0; white-space: pre-wrap;">${message}</p>
            </div>
            
            <p>Please acknowledge receipt of this message and provide an update at your earliest convenience.</p>
            
            <p>Thank you for your continued partnership.</p>
            
            <p>Best regards,<br><strong>AI CRM Logistics Team</strong></p>
          </div>
          
          <div class="footer">
            <p><strong>AI CRM Logistics System</strong></p>
            <p>This is an automated message. Please contact our admin team for inquiries.</p>
            <p style="margin-top: 10px; font-size: 12px;">
              © ${new Date().getFullYear()} AI CRM Logistics. All rights reserved.
            </p>
          </div>
        </div>
      </body>
      </html>
    `;
  }

  getPurchaseOrderTemplate(supplierName, items, orderNumber, deliveryDate) {
    const itemsHtml = items.map(item => `
      <div style="display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #e5e7eb;">
        <span style="font-weight: bold; color: #6b7280;">${item.productName || item.name}</span>
        <span style="color: #111827;">${item.quantity} ${item.unit || 'units'}</span>
      </div>
    `).join('');

    return `
      <!DOCTYPE html>
      <html>
      <head>
        <style>
          body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
          .container { max-width: 600px; margin: 0 auto; padding: 20px; }
          .header { background: #3b82f6; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }
          .content { background: #f9fafb; padding: 30px; border: 1px solid #e5e7eb; }
          .po-details { background: white; padding: 20px; border-radius: 8px; margin: 20px 0; }
          .footer { background: #1f2937; color: #9ca3af; padding: 20px; text-align: center; border-radius: 0 0 8px 8px; font-size: 14px; }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="header">
            <h1>📄 Purchase Order</h1>
          </div>
          
          <div class="content">
            <p>Dear ${supplierName},</p>
            
            <p>We are pleased to place the following purchase order with you:</p>
            
            <div class="po-details">
              <h3 style="margin-top: 0; color: #3b82f6;">Order #${orderNumber}</h3>
              
              <div style="margin: 20px 0;">
                <p style="margin: 5px 0;"><strong>Order Date:</strong> ${new Date().toLocaleDateString()}</p>
                <p style="margin: 5px 0;"><strong>Expected Delivery:</strong> ${new Date(deliveryDate).toLocaleDateString()}</p>
              </div>
              
              <h4 style="color: #6b7280; margin-bottom: 10px;">Items Ordered:</h4>
              ${itemsHtml}
            </div>
            
            <p><strong>Important:</strong></p>
            <ul>
              <li>Please confirm receipt of this purchase order</li>
              <li>Notify us immediately if you cannot meet the delivery date</li>
              <li>Ensure all items meet our quality standards</li>
            </ul>
            
            <p>Thank you for your continued service.</p>
            
            <p>Best regards,<br><strong>Procurement Team</strong><br>AI CRM Logistics</p>
          </div>
          
          <div class="footer">
            <p><strong>AI CRM Logistics System</strong></p>
            <p style="margin-top: 10px; font-size: 12px;">
              © ${new Date().getFullYear()} AI CRM Logistics. All rights reserved.
            </p>
          </div>
        </div>
      </body>
      </html>
    `;
  }

  getShipmentTemplate(trackingNumber, estimatedDelivery) {
    return `
      <!DOCTYPE html>
      <html>
      <head>
        <style>
          body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
          .container { max-width: 600px; margin: 0 auto; padding: 20px; }
          .header { background: #10b981; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }
          .content { background: #f9fafb; padding: 30px; border: 1px solid #e5e7eb; }
          .tracking-box { background: white; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center; border: 2px dashed #10b981; }
          .tracking-number { font-size: 24px; font-weight: bold; color: #10b981; letter-spacing: 2px; }
          .footer { background: #1f2937; color: #9ca3af; padding: 20px; text-align: center; border-radius: 0 0 8px 8px; font-size: 14px; }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="header">
            <h1>📦 Your Order Has Been Shipped!</h1>
          </div>
          
          <div class="content">
            <p>Great news! Your order is on its way.</p>
            
            <div class="tracking-box">
              <p style="margin: 0; color: #6b7280; font-size: 14px;">Tracking Number</p>
              <p class="tracking-number">${trackingNumber || 'TRK' + Date.now()}</p>
              <p style="margin: 10px 0 0 0; color: #6b7280; font-size: 14px;">
                Estimated Delivery: <strong>${estimatedDelivery ? new Date(estimatedDelivery).toLocaleDateString() : 'Within 3-5 business days'}</strong>
              </p>
            </div>
            
            <p>You can track your shipment using the tracking number provided above.</p>
            
            <p>Thank you for your order!</p>
          </div>
          
          <div class="footer">
            <p><strong>AI CRM Logistics System</strong></p>
            <p style="margin-top: 10px; font-size: 12px;">
              © ${new Date().getFullYear()} AI CRM Logistics. All rights reserved.
            </p>
          </div>
        </div>
      </body>
      </html>
    `;
  }
}

export default new EmailService();
