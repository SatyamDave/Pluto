import React, { useState } from 'react';
import { 
  Button, 
  Modal, 
  Form, 
  Input, 
  Select, 
  Typography, 
  Space, 
  message, 
  Card,
  Rate,
  Divider,
  Alert
} from 'antd';
import { 
  BugOutlined, 
  BulbOutlined, 
  MessageOutlined,
  GithubOutlined,
  SlackOutlined,
  MailOutlined,
  SmileOutlined,
  MehOutlined,
  FrownOutlined
} from '@ant-design/icons';
import posthog from 'posthog-js';

const { Title, Paragraph, Text } = Typography;
const { TextArea } = Input;
const { Option } = Select;

interface FeedbackWidgetProps {
  visible: boolean;
  onClose: () => void;
  userEmail?: string;
  userTier?: string;
}

const FeedbackWidget: React.FC<FeedbackWidgetProps> = ({ 
  visible, 
  onClose, 
  userEmail, 
  userTier 
}) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [feedbackType, setFeedbackType] = useState<'bug' | 'feature' | 'general'>('general');
  const [satisfaction, setSatisfaction] = useState<number>(0);

  const handleSubmit = async (values: any) => {
    setLoading(true);
    try {
      // Prepare feedback data
      const feedbackData = {
        type: feedbackType,
        title: values.title,
        description: values.description,
        priority: values.priority,
        category: values.category,
        satisfaction: satisfaction,
        userEmail: userEmail,
        userTier: userTier,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        url: window.location.href
      };

      // Submit to backend
      const response = await fetch('/api/feedback/submit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(feedbackData),
      });

      if (response.ok) {
        const result = await response.json();
        
        // Track feedback submission
        posthog.capture('feedback_submitted', {
          type: feedbackType,
          priority: values.priority,
          satisfaction: satisfaction,
          hasGitHubIssue: !!result.githubIssueUrl
        });

        message.success('Thank you for your feedback! We\'ll review it shortly.');
        
        // Show GitHub issue link if created
        if (result.githubIssueUrl) {
          Modal.info({
            title: 'GitHub Issue Created',
            content: (
              <div>
                <p>We\'ve created a GitHub issue to track your feedback:</p>
                <a href={result.githubIssueUrl} target="_blank" rel="noopener noreferrer">
                  {result.githubIssueUrl}
                </a>
              </div>
            ),
            onOk() {
              form.resetFields();
              setFeedbackType('general');
              setSatisfaction(0);
              onClose();
            }
          });
        } else {
          form.resetFields();
          setFeedbackType('general');
          setSatisfaction(0);
          onClose();
        }
      } else {
        throw new Error('Failed to submit feedback');
      }
    } catch (error) {
      message.error('Failed to submit feedback. Please try again.');
      posthog.capture('feedback_submission_error', {
        type: feedbackType,
        error: error.message
      });
    } finally {
      setLoading(false);
    }
  };

  const getFeedbackIcon = () => {
    switch (feedbackType) {
      case 'bug':
        return <BugOutlined style={{ color: '#ff4d4f' }} />;
      case 'feature':
        return <BulbOutlined style={{ color: '#1890ff' }} />;
      default:
        return <MessageOutlined style={{ color: '#52c41a' }} />;
    }
  };

  const getFeedbackTitle = () => {
    switch (feedbackType) {
      case 'bug':
        return 'Report a Bug';
      case 'feature':
        return 'Request a Feature';
      default:
        return 'Send Feedback';
    }
  };

  const getFeedbackDescription = () => {
    switch (feedbackType) {
      case 'bug':
        return 'Help us improve by reporting any issues you encounter.';
      case 'feature':
        return 'Share your ideas for new features or improvements.';
      default:
        return 'We\'d love to hear your thoughts about AI Market Terminal.';
    }
  };

  return (
    <Modal
      title={
        <Space>
          {getFeedbackIcon()}
          <span>{getFeedbackTitle()}</span>
        </Space>
      }
      open={visible}
      onCancel={onClose}
      footer={null}
      width={600}
      destroyOnClose
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        initialValues={{
          priority: 'medium',
          category: 'general'
        }}
      >
        {/* Feedback Type Selection */}
        <Card size="small" style={{ marginBottom: 24 }}>
          <Space direction="vertical" style={{ width: '100%' }}>
            <Title level={5}>What type of feedback do you have?</Title>
            <Space wrap>
              <Button
                type={feedbackType === 'bug' ? 'primary' : 'default'}
                icon={<BugOutlined />}
                onClick={() => setFeedbackType('bug')}
              >
                Bug Report
              </Button>
              <Button
                type={feedbackType === 'feature' ? 'primary' : 'default'}
                icon={<BulbOutlined />}
                onClick={() => setFeedbackType('feature')}
              >
                Feature Request
              </Button>
              <Button
                type={feedbackType === 'general' ? 'primary' : 'default'}
                icon={<MessageOutlined />}
                onClick={() => setFeedbackType('general')}
              >
                General Feedback
              </Button>
            </Space>
          </Space>
        </Card>

        <Paragraph style={{ marginBottom: 24 }}>
          {getFeedbackDescription()}
        </Paragraph>

        {/* Satisfaction Rating */}
        <Form.Item label="How satisfied are you with AI Market Terminal?">
          <Space direction="vertical" style={{ width: '100%' }}>
            <Rate 
              value={satisfaction} 
              onChange={setSatisfaction}
              character={({ index }) => {
                if (index === 0) return <FrownOutlined />;
                if (index === 1) return <MehOutlined />;
                if (index === 2) return <SmileOutlined />;
                if (index === 3) return <SmileOutlined />;
                return <SmileOutlined />;
              }}
            />
            <Text type="secondary">
              {satisfaction === 0 && 'Not satisfied'}
              {satisfaction === 1 && 'Somewhat satisfied'}
              {satisfaction === 2 && 'Satisfied'}
              {satisfaction === 3 && 'Very satisfied'}
              {satisfaction === 4 && 'Extremely satisfied'}
            </Text>
          </Space>
        </Form.Item>

        {/* Title */}
        <Form.Item
          name="title"
          label="Title"
          rules={[{ required: true, message: 'Please provide a title' }]}
        >
          <Input 
            placeholder={
              feedbackType === 'bug' ? 'Brief description of the issue' :
              feedbackType === 'feature' ? 'Feature name or description' :
              'Feedback title'
            }
          />
        </Form.Item>

        {/* Category */}
        <Form.Item
          name="category"
          label="Category"
          rules={[{ required: true, message: 'Please select a category' }]}
        >
          <Select placeholder="Select a category">
            {feedbackType === 'bug' && (
              <>
                <Option value="ui-ux">UI/UX Issue</Option>
                <Option value="performance">Performance Issue</Option>
                <Option value="data">Data/Accuracy Issue</Option>
                <Option value="integration">Integration Issue</Option>
                <Option value="security">Security Issue</Option>
                <Option value="other">Other</Option>
              </>
            )}
            {feedbackType === 'feature' && (
              <>
                <Option value="trading">Trading Features</Option>
                <Option value="analytics">Analytics & Reporting</Option>
                <Option value="ai">AI & Machine Learning</Option>
                <Option value="mobile">Mobile App</Option>
                <Option value="integration">Third-party Integration</Option>
                <Option value="other">Other</Option>
              </>
            )}
            {feedbackType === 'general' && (
              <>
                <Option value="general">General Feedback</Option>
                <Option value="pricing">Pricing</Option>
                <Option value="support">Support</Option>
                <Option value="documentation">Documentation</Option>
                <Option value="other">Other</Option>
              </>
            )}
          </Select>
        </Form.Item>

        {/* Priority */}
        <Form.Item
          name="priority"
          label="Priority"
          rules={[{ required: true, message: 'Please select priority' }]}
        >
          <Select placeholder="Select priority">
            <Option value="low">Low - Nice to have</Option>
            <Option value="medium">Medium - Important</Option>
            <Option value="high">High - Critical</Option>
          </Select>
        </Form.Item>

        {/* Description */}
        <Form.Item
          name="description"
          label="Description"
          rules={[{ required: true, message: 'Please provide details' }]}
        >
          <TextArea
            rows={6}
            placeholder={
              feedbackType === 'bug' ? 
              'Please describe the issue in detail. Include steps to reproduce, expected vs actual behavior, and any error messages.' :
              feedbackType === 'feature' ?
              'Please describe the feature you\'d like to see. Include use cases, benefits, and any specific requirements.' :
              'Please share your thoughts, suggestions, or concerns about AI Market Terminal.'
            }
          />
        </Form.Item>

        {/* Contact Information */}
        {!userEmail && (
          <Form.Item
            name="email"
            label="Email (optional)"
            rules={[{ type: 'email', message: 'Please enter a valid email' }]}
          >
            <Input 
              placeholder="Your email address"
              prefix={<MailOutlined />}
            />
          </Form.Item>
        )}

        <Divider />

        {/* Support Channels */}
        <Alert
          message="Need immediate help?"
          description={
            <Space direction="vertical">
              <div>
                <GithubOutlined /> 
                <a href="https://github.com/your-repo/issues" target="_blank" rel="noopener noreferrer">
                  GitHub Issues
                </a> - Track bugs and feature requests
              </div>
              <div>
                <SlackOutlined /> 
                <a href="https://slack.com/app_redirect?channel=beta-support" target="_blank" rel="noopener noreferrer">
                  Slack Community
                </a> - Get help from the community
              </div>
              <div>
                <MailOutlined /> 
                <a href="mailto:beta-support@aimarketterminal.com">
                  Email Support
                </a> - Direct support for beta users
              </div>
            </Space>
          }
          type="info"
          showIcon
          style={{ marginBottom: 24 }}
        />

        {/* Submit Button */}
        <Form.Item>
          <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
            <Button onClick={onClose}>
              Cancel
            </Button>
            <Button 
              type="primary" 
              htmlType="submit" 
              loading={loading}
              icon={getFeedbackIcon()}
            >
              Submit Feedback
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default FeedbackWidget;
