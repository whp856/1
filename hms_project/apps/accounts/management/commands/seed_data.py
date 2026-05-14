from django.core.management.base import BaseCommand
from django.db import transaction
from datetime import date, timedelta

from apps.accounts.models import User
from apps.departments.models import Department
from apps.patients.models import Patient
from apps.pharmacy.models import Medicine


class Command(BaseCommand):
    help = '初始化系统种子数据（科室、用户、药品）'

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        self.stdout.write('开始初始化种子数据...')

        departments = self._create_departments()
        self._create_users(departments)
        self._create_medicines()
        self._create_patients()

        self.stdout.write(self.style.SUCCESS('种子数据初始化完成！'))
        self.stdout.write('管理员账号: admin / admin123')
        self.stdout.write('医生账号: doctor1 / doctor123')
        self.stdout.write('护士账号: nurse1 / nurse123')
        self.stdout.write('药剂师账号: pharm1 / pharm123')

    def _create_departments(self) -> dict:
        dept_data = [
            ('内科', '诊治内科疾病，包括心血管、呼吸、消化、内分泌等'),
            ('外科', '诊治外科疾病，开展各类手术及术后管理'),
            ('儿科', '诊治0-14岁儿童的各类疾病'),
            ('妇产科', '妇科疾病诊治及孕产妇保健管理'),
            ('骨科', '骨骼、关节、脊柱相关疾病诊治'),
            ('皮肤科', '各类皮肤疾病诊治'),
            ('眼科', '眼部疾病诊治及视力矫正'),
            ('耳鼻喉科', '耳、鼻、喉相关疾病诊治'),
        ]
        depts = {}
        for name, desc in dept_data:
            dept, created = Department.objects.get_or_create(
                name=name, defaults={'description': desc},
            )
            depts[name] = dept
            if created:
                self.stdout.write(f'  创建科室: {name}')
        return depts

    def _create_users(self, depts: dict) -> None:
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin', password='admin123',
                full_name='系统管理员', role='admin', phone='13800000001',
            )
            self.stdout.write('  创建管理员: admin')

        doctors = [
            ('doctor1', 'doctor123', '张明远', depts.get('内科')),
            ('doctor2', 'doctor123', '李淑芬', depts.get('儿科')),
            ('doctor3', 'doctor123', '王志强', depts.get('外科')),
        ]
        for username, password, full_name, dept in doctors:
            if not User.objects.filter(username=username).exists():
                User.objects.create_user(
                    username=username, password=password,
                    full_name=full_name, role='doctor',
                    department=dept, phone='13800000002',
                )
                self.stdout.write(f'  创建医生: {full_name}')

        nurses = [
            ('nurse1', 'nurse123', '陈丽华', depts.get('内科')),
            ('nurse2', 'nurse123', '赵红梅', depts.get('外科')),
        ]
        for username, password, full_name, dept in nurses:
            if not User.objects.filter(username=username).exists():
                User.objects.create_user(
                    username=username, password=password,
                    full_name=full_name, role='nurse',
                    department=dept, phone='13800000003',
                )
                self.stdout.write(f'  创建护士: {full_name}')

        pharms = [
            ('pharm1', 'pharm123', '刘建国', None),
            ('pharm2', 'pharm123', '孙秀英', None),
        ]
        for username, password, full_name, dept in pharms:
            if not User.objects.filter(username=username).exists():
                User.objects.create_user(
                    username=username, password=password,
                    full_name=full_name, role='pharmacist',
                    phone='13800000004',
                )
                self.stdout.write(f'  创建药剂师: {full_name}')

    def _create_medicines(self) -> None:
        medicines = [
            ('阿莫西林胶囊', '0.25g*24粒', '华北制药', 12.50, 100, 'western', date.today() + timedelta(days=365)),
            ('头孢克洛胶囊', '0.25g*12粒', '广州白云山', 28.00, 80, 'western', date.today() + timedelta(days=400)),
            ('布洛芬缓释胶囊', '0.3g*20粒', '中美史克', 18.50, 120, 'western', date.today() + timedelta(days=500)),
            ('对乙酰氨基酚片', '0.5g*12片', '上海强生', 8.00, 150, 'western', date.today() + timedelta(days=300)),
            ('阿奇霉素片', '0.25g*6片', '辉瑞制药', 35.00, 60, 'western', date.today() + timedelta(days=200)),
            ('板蓝根颗粒', '10g*20袋', '北京同仁堂', 15.00, 200, 'chinese_patent', date.today() + timedelta(days=600)),
            ('连花清瘟胶囊', '0.35g*36粒', '以岭药业', 22.00, 90, 'chinese_patent', date.today() + timedelta(days=450)),
            ('双黄连口服液', '10ml*10支', '哈药集团', 16.00, 100, 'chinese_patent', date.today() + timedelta(days=350)),
            ('红霉素软膏', '10g/支', '云南白药', 5.50, 80, 'external', date.today() + timedelta(days=700)),
            ('硝酸咪康唑乳膏', '20g/支', '西安杨森', 12.00, 60, 'external', date.today() + timedelta(days=500)),
            ('葡萄糖注射液', '5% 250ml', '科伦药业', 4.50, 200, 'injection', date.today() + timedelta(days=180)),
            ('氯化钠注射液', '0.9% 250ml', '科伦药业', 3.80, 300, 'injection', date.today() + timedelta(days=200)),
            ('奥美拉唑肠溶胶囊', '20mg*14粒', '阿斯利康', 42.00, 50, 'western', date.today() + timedelta(days=365)),
            ('蒙脱石散', '3g*10袋', '益普生', 18.00, 70, 'western', date.today() + timedelta(days=400)),
            ('复方甘草片', '100片/瓶', '广州白云山', 9.50, 110, 'western', date.today() + timedelta(days=250)),
        ]

        for name, spec, mfr, price, stock, cat, expiry in medicines:
            try:
                pinyin = ''.join([w[0].upper() for w in _get_pinyin(name)])
            except Exception:
                pinyin = name[:10].upper()
            obj, created = Medicine.objects.get_or_create(
                name=name,
                defaults={
                    'pinyin_code': pinyin,
                    'specification': spec,
                    'manufacturer': mfr,
                    'unit_price': price,
                    'stock_quantity': stock,
                    'warning_stock': 10,
                    'expiry_date': expiry,
                    'category': cat,
                },
            )
            if created:
                self.stdout.write(f'  创建药品: {name}')

    def _create_patients(self) -> None:
        if Patient.objects.exists():
            return
        patients = [
            ('110101199001011234', '王建国', 'male', 36, '13900001111', '青霉素过敏'),
            ('110101198505152345', '李秀兰', 'female', 41, '13900002222', ''),
            ('110101201003201234', '张小明', 'male', 16, '13900003333', ''),
            ('110101197808081234', '赵德胜', 'male', 48, '13900004444', '磺胺类药物过敏'),
        ]
        for id_card, name, gender, age, phone, allergy in patients:
            Patient.objects.create(
                id_card=id_card, name=name, gender=gender, age=age, phone=phone, allergy_history=allergy,
            )
            self.stdout.write(f'  创建患者: {name}')


def _get_pinyin(text: str) -> list[str]:
    try:
        from pypinyin import lazy_pinyin
        return lazy_pinyin(text)
    except ImportError:
        return list(text)
