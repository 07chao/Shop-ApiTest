import React, { useState } from 'react'
import { Card, Typography, Form, Input, Button, Upload, message, Tabs } from 'antd'
import { UserOutlined, MailOutlined, PhoneOutlined, UploadOutlined, LockOutlined } from '@ant-design/icons'

const { Title } = Typography
const { TabPane } = Tabs

const Profile = () => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)

  // 模拟用户数据
  const userInfo = {
    username: '张三',
    email: 'zhangsan@example.com',
    phone: '138****1234'
  }

  const onFinish = async (values) => {
    setLoading(true)
    try {
      // 这里应该调用更新用户信息的API
      console.log('Received values of form: ', values)
      message.success('信息更新成功')
    } catch (error) {
      message.error('信息更新失败: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  const onPasswordFinish = async (values) => {
    setLoading(true)
    try {
      // 这里应该调用修改密码的API
      console.log('Received password values: ', values)
      message.success('密码修改成功')
    } catch (error) {
      message.error('密码修改失败: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  const beforeUpload = (file) => {
    const isJpgOrPng = file.type === 'image/jpeg' || file.type === 'image/png'
    if (!isJpgOrPng) {
      message.error('只能上传 JPG/PNG 格式的图片!')
    }
    const isLt2M = file.size / 1024 / 1024 < 2
    if (!isLt2M) {
      message.error('图片大小不能超过 2MB!')
    }
    return isJpgOrPng && isLt2M
  }

  const handleChange = info => {
    if (info.file.status === 'done') {
      message.success('头像上传成功')
    } else if (info.file.status === 'error') {
      message.error('头像上传失败')
    }
  }

  return (
    <div>
      <Title level={2}>个人中心</Title>
      
      <Tabs defaultActiveKey="1">
        <TabPane tab="基本信息" key="1">
          <Card>
            <div style={{ display: 'flex', marginBottom: 30 }}>
              <div style={{ marginRight: 50 }}>
                <Upload
                  name="avatar"
                  listType="picture-card"
                  className="avatar-uploader"
                  showUploadList={false}
                  beforeUpload={beforeUpload}
                  onChange={handleChange}
                >
                  <div>
                    <div style={{ 
                      width: 100, 
                      height: 100, 
                      borderRadius: '50%', 
                      backgroundColor: '#f0f0f0',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}>
                      <UserOutlined style={{ fontSize: 40 }} />
                    </div>
                    <div style={{ marginTop: 10 }}>点击上传头像</div>
                  </div>
                </Upload>
              </div>
              
              <div>
                <Form
                  form={form}
                  name="profile"
                  onFinish={onFinish}
                  initialValues={userInfo}
                  labelCol={{ span: 4 }}
                  wrapperCol={{ span: 16 }}
                >
                  <Form.Item
                    label="用户名"
                    name="username"
                    rules={[{ required: true, message: '请输入用户名!' }]}
                  >
                    <Input prefix={<UserOutlined />} />
                  </Form.Item>
                  
                  <Form.Item
                    label="邮箱"
                    name="email"
                    rules={[
                      { required: true, message: '请输入邮箱!' },
                      { type: 'email', message: '请输入有效的邮箱地址!' }
                    ]}
                  >
                    <Input prefix={<MailOutlined />} />
                  </Form.Item>
                  
                  <Form.Item
                    label="手机号"
                    name="phone"
                  >
                    <Input prefix={<PhoneOutlined />} />
                  </Form.Item>
                  
                  <Form.Item wrapperCol={{ offset: 4, span: 16 }}>
                    <Button type="primary" htmlType="submit" loading={loading}>
                      更新信息
                    </Button>
                  </Form.Item>
                </Form>
              </div>
            </div>
          </Card>
        </TabPane>
        
        <TabPane tab="修改密码" key="2">
          <Card>
            <Form
              name="password"
              onFinish={onPasswordFinish}
              labelCol={{ span: 4 }}
              wrapperCol={{ span: 16 }}
            >
              <Form.Item
                label="当前密码"
                name="currentPassword"
                rules={[{ required: true, message: '请输入当前密码!' }]}
              >
                <Input.Password prefix={<LockOutlined />} />
              </Form.Item>
              
              <Form.Item
                label="新密码"
                name="newPassword"
                rules={[
                  { required: true, message: '请输入新密码!' },
                  { min: 6, message: '密码至少6位!' }
                ]}
              >
                <Input.Password prefix={<LockOutlined />} />
              </Form.Item>
              
              <Form.Item
                label="确认密码"
                name="confirmPassword"
                dependencies={['newPassword']}
                rules={[
                  { required: true, message: '请确认新密码!' },
                  ({ getFieldValue }) => ({
                    validator(_, value) {
                      if (!value || getFieldValue('newPassword') === value) {
                        return Promise.resolve()
                      }
                      return Promise.reject(new Error('两次输入的密码不一致!'))
                    },
                  }),
                ]}
              >
                <Input.Password prefix={<LockOutlined />} />
              </Form.Item>
              
              <Form.Item wrapperCol={{ offset: 4, span: 16 }}>
                <Button type="primary" htmlType="submit" loading={loading}>
                  修改密码
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </TabPane>
      </Tabs>
    </div>
  )
}

export default Profile