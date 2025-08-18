import React, { useState, useRef } from 'react';
import { 
  Button, 
  Card, 
  Typography, 
  Space, 
  Input, 
  message, 
  Modal,
  Row,
  Col,
  Statistic,
  Divider
} from 'antd';
import { 
  ShareAltOutlined, 
  DownloadOutlined, 
  LinkOutlined,
  TwitterOutlined,
  LinkedinOutlined,
  FacebookOutlined,
  CopyOutlined
} from '@ant-design/icons';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import html2canvas from 'html2canvas';
import posthog from 'posthog-js';

const { Title, Paragraph, Text } = Typography;

interface ShareAnalysisProps {
  analysisData: {
    symbol: string;
    strategy: string;
    totalReturn: number;
    sharpeRatio: number;
    maxDrawdown: number;
    chartData: Array<{
      date: string;
      value: number;
      benchmark: number;
    }>;
  };
  onShare?: (shareUrl: string) => void;
}

const ShareAnalysis: React.FC<ShareAnalysisProps> = ({ analysisData, onShare }) => {
  const [shareModalVisible, setShareModalVisible] = useState(false);
  const [shareUrl, setShareUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const chartRef = useRef<HTMLDivElement>(null);

  const generateShareUrl = async () => {
    setLoading(true);
    try {
      // Create shareable analysis data
      const shareData = {
        symbol: analysisData.symbol,
        strategy: analysisData.strategy,
        totalReturn: analysisData.totalReturn,
        sharpeRatio: analysisData.sharpeRatio,
        maxDrawdown: analysisData.maxDrawdown,
        timestamp: new Date().toISOString(),
        source: 'ai-market-terminal'
      };

      // In a real implementation, this would save to your backend
      const response = await fetch('/api/analysis/share', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(shareData),
      });

      if (response.ok) {
        const { shareId } = await response.json();
        const url = `${window.location.origin}/analysis/${shareId}`;
        setShareUrl(url);
        
        // Track share generation
        posthog.capture('analysis_share_generated', {
          symbol: analysisData.symbol,
          strategy: analysisData.strategy,
          totalReturn: analysisData.totalReturn,
          shareUrl: url
        });
      } else {
        throw new Error('Failed to generate share URL');
      }
    } catch (error) {
      message.error('Failed to generate share URL');
    } finally {
      setLoading(false);
    }
  };

  const downloadChart = async () => {
    if (!chartRef.current) return;

    try {
      setLoading(true);
      
      // Add watermark to chart
      const watermark = document.createElement('div');
      watermark.style.position = 'absolute';
      watermark.style.top = '10px';
      watermark.style.right = '10px';
      watermark.style.fontSize = '12px';
      watermark.style.color = 'rgba(0,0,0,0.5)';
      watermark.style.zIndex = '1000';
      watermark.textContent = 'AI Market Terminal';
      
      chartRef.current.appendChild(watermark);

      // Capture chart as image
      const canvas = await html2canvas(chartRef.current, {
        backgroundColor: '#ffffff',
        scale: 2,
        useCORS: true
      });

      // Remove watermark
      chartRef.current.removeChild(watermark);

      // Download image
      const link = document.createElement('a');
      link.download = `${analysisData.symbol}-${analysisData.strategy}-analysis.png`;
      link.href = canvas.toDataURL();
      link.click();

      // Track download
      posthog.capture('analysis_chart_downloaded', {
        symbol: analysisData.symbol,
        strategy: analysisData.strategy,
        totalReturn: analysisData.totalReturn
      });

      message.success('Chart downloaded successfully!');
    } catch (error) {
      message.error('Failed to download chart');
    } finally {
      setLoading(false);
    }
  };

  const copyShareUrl = () => {
    navigator.clipboard.writeText(shareUrl);
    message.success('Share URL copied to clipboard!');
    
    posthog.capture('analysis_share_url_copied', {
      shareUrl
    });
  };

  const shareToSocial = (platform: string) => {
    const text = `Check out this ${analysisData.strategy} analysis for ${analysisData.symbol} on AI Market Terminal! ${analysisData.totalReturn > 0 ? '+' : ''}${(analysisData.totalReturn * 100).toFixed(1)}% return`;
    
    let url = '';
    switch (platform) {
      case 'twitter':
        url = `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(shareUrl)}`;
        break;
      case 'linkedin':
        url = `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(shareUrl)}`;
        break;
      case 'facebook':
        url = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareUrl)}`;
        break;
    }
    
    if (url) {
      window.open(url, '_blank');
      
      posthog.capture('analysis_shared_to_social', {
        platform,
        symbol: analysisData.symbol,
        strategy: analysisData.strategy,
        shareUrl
      });
    }
  };

  const handleShare = () => {
    setShareModalVisible(true);
    generateShareUrl();
  };

  return (
    <>
      <Card 
        title={
          <Space>
            <ShareAltOutlined />
            <span>Share Analysis</span>
          </Space>
        }
        extra={
          <Space>
            <Button 
              icon={<DownloadOutlined />} 
              onClick={downloadChart}
              loading={loading}
            >
              Download Chart
            </Button>
            <Button 
              type="primary" 
              icon={<ShareAltOutlined />} 
              onClick={handleShare}
            >
              Share
            </Button>
          </Space>
        }
      >
        <div ref={chartRef} style={{ position: 'relative', background: 'white', padding: '20px' }}>
          <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
            <Col span={8}>
              <Statistic
                title="Total Return"
                value={analysisData.totalReturn * 100}
                suffix="%"
                valueStyle={{ 
                  color: analysisData.totalReturn >= 0 ? '#3f8600' : '#cf1322' 
                }}
              />
            </Col>
            <Col span={8}>
              <Statistic
                title="Sharpe Ratio"
                value={analysisData.sharpeRatio}
                precision={2}
              />
            </Col>
            <Col span={8}>
              <Statistic
                title="Max Drawdown"
                value={analysisData.maxDrawdown * 100}
                suffix="%"
                valueStyle={{ color: '#cf1322' }}
              />
            </Col>
          </Row>

          <Divider />

          <Title level={4}>
            {analysisData.symbol} - {analysisData.strategy} Strategy
          </Title>
          
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={analysisData.chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="date" 
                tick={{ fontSize: 12 }}
                tickFormatter={(value) => new Date(value).toLocaleDateString()}
              />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip 
                labelFormatter={(value) => new Date(value).toLocaleDateString()}
                formatter={(value: number) => [`$${value.toFixed(2)}`, 'Portfolio Value']}
              />
              <Line 
                type="monotone" 
                dataKey="value" 
                stroke="#1890ff" 
                strokeWidth={2}
                dot={false}
              />
              <Line 
                type="monotone" 
                dataKey="benchmark" 
                stroke="#d9d9d9" 
                strokeWidth={1}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>

          <div style={{ 
            textAlign: 'center', 
            marginTop: 16, 
            fontSize: 12, 
            color: '#666' 
          }}>
            Generated by AI Market Terminal • {new Date().toLocaleDateString()}
          </div>
        </div>
      </Card>

      <Modal
        title="Share Analysis"
        open={shareModalVisible}
        onCancel={() => setShareModalVisible(false)}
        footer={null}
        width={600}
      >
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div>
            <Title level={5}>Share URL</Title>
            <Input.Group compact>
              <Input
                style={{ width: 'calc(100% - 100px)' }}
                value={shareUrl}
                placeholder="Generating share URL..."
                readOnly
              />
              <Button 
                icon={<CopyOutlined />} 
                onClick={copyShareUrl}
                disabled={!shareUrl}
              >
                Copy
              </Button>
            </Input.Group>
          </div>

          <div>
            <Title level={5}>Share to Social Media</Title>
            <Space>
              <Button 
                icon={<TwitterOutlined />} 
                onClick={() => shareToSocial('twitter')}
                disabled={!shareUrl}
              >
                Twitter
              </Button>
              <Button 
                icon={<LinkedinOutlined />} 
                onClick={() => shareToSocial('linkedin')}
                disabled={!shareUrl}
              >
                LinkedIn
              </Button>
              <Button 
                icon={<FacebookOutlined />} 
                onClick={() => shareToSocial('facebook')}
                disabled={!shareUrl}
              >
                Facebook
              </Button>
            </Space>
          </div>

          <div>
            <Title level={5}>Analysis Summary</Title>
            <Row gutter={[16, 16]}>
              <Col span={8}>
                <Statistic
                  title="Symbol"
                  value={analysisData.symbol}
                  valueStyle={{ fontSize: 16 }}
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="Strategy"
                  value={analysisData.strategy}
                  valueStyle={{ fontSize: 16 }}
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="Return"
                  value={analysisData.totalReturn * 100}
                  suffix="%"
                  valueStyle={{ 
                    fontSize: 16,
                    color: analysisData.totalReturn >= 0 ? '#3f8600' : '#cf1322' 
                  }}
                />
              </Col>
            </Row>
          </div>

          <Paragraph style={{ fontSize: 12, color: '#666', textAlign: 'center' }}>
            When someone clicks your share link, they'll see this analysis and can sign up for AI Market Terminal to run their own analyses.
          </Paragraph>
        </Space>
      </Modal>
    </>
  );
};

export default ShareAnalysis;
