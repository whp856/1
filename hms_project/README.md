# 医院管理系统 (HMS) - 部署运行指南

## 技术栈
- Python 3.12+ / Django 5.1+
- MySQL 8.0+
- 纯 CSS + Vanilla JavaScript

---

## 1. 环境准备

### 1.1 安装 Python 依赖
```bash
cd hms_project
pip install django mysqlclient openpyxl pydantic cryptography
```

### 1.2 创建 MySQL 数据库
登录 MySQL 执行：
```sql
CREATE DATABASE hms_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

---

## 2. 配置数据库连接

复制 `.env.example` 为 `.env`，填入你的 MySQL 密码：

```bash
cp .env.example .env
```

编辑 `.env` 文件内容：

```ini
SECRET_KEY=your-secret-key-change-me
DEBUG=True

DB_NAME=hms_db
DB_USER=root
DB_PASSWORD=你的MySQL密码
DB_HOST=localhost
DB_PORT=3306
```

> 不需要改 `hms/settings.py`，所有敏感配置都在 `.env` 中管理。`.env` 已被 `.gitignore` 排除，不会提交到 GitHub。

---

## 3. 数据库迁移

```bash
cd hms_project

# 生成迁移文件
python manage.py makemigrations accounts departments patients appointments medical pharmacy

# 执行迁移
python manage.py migrate
```

---

## 4. 初始化种子数据

```bash
python manage.py seed_data
```

执行后会自动创建：
| 角色 | 用户名 | 密码 |
|------|--------|------|
| 系统管理员 | admin | admin123 |
| 医生 | doctor1 | doctor123 |
| 医生 | doctor2 | doctor123 |
| 医生 | doctor3 | doctor123 |
| 护士 | nurse1 | nurse123 |
| 护士 | nurse2 | nurse123 |
| 药剂师 | pharm1 | pharm123 |
| 药剂师 | pharm2 | pharm123 |

同时初始化 8 个科室、15 种药品、4 位患者。

---

## 5. 启动服务

```bash
python manage.py runserver
```

浏览器访问：`http://127.0.0.1:8000`

---

## 6. 项目结构

```
hms_project/
├── manage.py
├── requirements.txt
├── hms/                          # 项目配置
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── accounts/                 # 用户认证 & RBAC
│   │   ├── models.py             # User 模型 (AbstractUser)
│   │   ├── views.py              # 登录/仪表盘/用户CRUD
│   │   ├── forms.py
│   │   ├── decorators.py         # 角色装饰器
│   │   ├── urls.py
│   │   └── management/commands/seed_data.py
│   ├── departments/              # 科室管理
│   │   ├── models.py
│   │   ├── views.py
│   │   └── urls.py
│   ├── patients/                 # 患者管理
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── forms.py
│   │   └── urls.py
│   ├── appointments/             # 挂号管理
│   │   ├── models.py             # Appointment + DoctorSchedule
│   │   ├── views.py
│   │   ├── forms.py
│   │   └── urls.py
│   ├── medical/                  # 诊疗管理
│   │   ├── models.py             # MedicalRecord + NursingRecord
│   │   ├── prescription_models.py # Prescription + PrescriptionItem
│   │   ├── views.py
│   │   ├── forms.py
│   │   └── urls.py
│   ├── pharmacy/                 # 药品库存
│   │   ├── models.py             # Medicine + StockIn/Out/Check
│   │   ├── views.py
│   │   ├── forms.py
│   │   └── urls.py
│   └── finance/                  # 财务统计
│       ├── views.py
│       └── urls.py
├── static/
│   ├── css/style.css             # 完整医疗风格样式
│   └── js/main.js
└── templates/
    ├── base.html                 # 基础布局模板
    ├── login.html
    ├── dashboard.html
    ├── accounts/
    ├── departments/
    ├── patients/
    ├── appointments/
    ├── medical/
    ├── pharmacy/
    └── finance/
```

---

## 7. 边界情况处理清单

| 类别 | 处理 |
|------|------|
| 用户认证 | 禁用账号无法登录，密码最小长度6位 |
| 权限控制 | 4角色RBAC，装饰器校验，视图层权限过滤 |
| 患者建档 | 身份证18位校验，重复身份证拦截，年龄0-150校验 |
| 号源管理 | 实时检查剩余号源，防止超卖，30分钟内不可取消 |
| 处方开立 | 库存实时校验，空处方不可提交，单价自动计算 |
| 发药确认 | 事务原子操作，库存扣减与出库记录同步 |
| 库存入库 | 自动累加库存数量 |
| 库存盘点 | 自动计算差异，差异不为0时高亮 |
| 药品预警 | 库存不足(≤阈值)、即将过期(30天内)自动标记 |
| 科室删除 | 有关联用户时禁止删除 |
| 处方驳回 | 药剂师可驳回至医生，记录驳回原因 |
| SQL注入 | 全部使用ORM参数化查询 |
| 跨站请求 | CSRF 保护全站开启 |
| 会话安全 | 4小时过期，浏览器关闭即失效 |
| 输入验证 | 前后端双重校验，Django Form 层完整校验 |
| 键盘快捷键 | Ctrl+S保存、Esc关闭弹窗、Enter提交 |

---

## 8. 一键启动（完整流程）

```bash
cd hms_project

# 1. 安装依赖
pip install -r requirements.txt

# 2. 创建数据库 (MySQL命令行中执行)
# CREATE DATABASE hms_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 3. 修改 hms/settings.py 中的数据库密码

# 4. 迁移
python manage.py makemigrations accounts departments patients appointments medical pharmacy
python manage.py migrate

# 5. 初始化数据
python manage.py seed_data

# 6. 启动
python manage.py runserver
```
