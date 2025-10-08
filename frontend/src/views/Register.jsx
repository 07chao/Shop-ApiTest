import React, { useState } from 'react'
import { Form, Input, Button, Card, Typography, message, Select } from 'antd'
import { UserOutlined, LockOutlined, MailOutlined } from '@ant-design/icons'
import { Link, useNavigate } from 'react-router-dom'

const { Title } = Typography
const { Option } = Select

const Register = () => {
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const onFinish = async (values) => {
    setLoading(true)
    try {
      // 这里应该调用注册API
      console.log('Received values of form: ', values)
      message.success('注册成功')
      navigate('/login')
    } catch (error) {
      message.error('注册失败: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
      <Card style={{ width: 400 }}>
        <Title level={3} style={{ textAlign: 'center' }}>用户注册</Title>
        <Form
          name="register"
          onFinish={onFinish}
        >
          <Form.Item
            name="username"
            rules={[{ required: true, message: '请输入用户名!' }]}
          >
            <Input prefix={<UserOutlined />} placeholder="用户名" />
          </Form.Item>

          <Form.Item
            name="email"
            rules={[
              { required: true, message: '请输入邮箱!' },
              { type: 'email', message: '请输入有效的邮箱地址!' }
            ]}
          >
            <Input prefix={<MailOutlined />} placeholder="邮箱" />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[
              { required: true, message: '请输入密码!' },
              { min: 6, message: '密码至少6位!' }
            ]}
          >
            <Input prefix={<LockOutlined />} type="password" placeholder="密码" />
          </Form.Item>

          <Form.Item
            name="confirm"
            dependencies={['password']}
            rules={[
              { required: true, message: '请确认密码!' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('password') === value) {
                    return Promise.resolve()
                  }
                  return Promise.reject(new Error('两次输入的密码不一致!'))
                },
              }),
            ]}
          >
            <Input prefix={<LockOutlined />} type="password" placeholder="确认密码" />
          </Form.Item>

          <Form.Item
            name="role"
            rules={[{ required: true, message: '请选择用户角色!' }]}
          >
            <Select placeholder="用户角色">
              <Option value="user">普通用户</Option>
              <Option value="merchant">商家</Option>
            </Select>
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block>
              注册
            </Button>
            或 <Link to="/login">已有账户? 立即登录</Link>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}

export default Register