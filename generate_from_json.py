import json
import os
from collections import defaultdict

def generate_from_json():
    # 定义文件路径
    dist_dir = 'dist'
    provinces_file = os.path.join(dist_dir, 'provinces.json')
    cities_file = os.path.join(dist_dir, 'cities.json')
    areas_file = os.path.join(dist_dir, 'areas.json')
    streets_file = os.path.join(dist_dir, 'streets.json')
    villages_file = os.path.join(dist_dir, 'villages.json')

    # 创建输出目录
    output_dir = 'areas'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print("开始从 JSON 文件生成数据结构...")

    try:
        # 1. 加载 provinces, cities, 和 areas 数据到内存
        print("正在加载 provinces, cities, areas...")
        with open(provinces_file, 'r', encoding='utf-8') as f:
            provinces_data = json.load(f)
        
        with open(cities_file, 'r', encoding='utf-8') as f:
            cities_data = json.load(f)
            
        with open(areas_file, 'r', encoding='utf-8') as f:
            areas_data = json.load(f)

        # 创建 province 和 city 的快速查找字典
        provinces_map = {p['code']: p['name'] for p in provinces_data}
        cities_map = {c['code']: c for c in cities_data}

        # 2. 处理 villages.json
        print("正在处理 villages.json...")
        villages_by_street = defaultdict(list)
        with open(villages_file, 'r', encoding='utf-8') as f:
            villages_list = json.load(f)
            for village in villages_list:
                street_code = village.get('streetCode')
                if street_code:
                    villages_by_street[street_code].append({
                        "code": village.get('code'),
                        "name": village.get('name'),
                        "streetCode": street_code
                    })
        print(f"处理完成，找到 {len(villages_list)} 个村庄，归属于 {len(villages_by_street)} 个街道。")

        # 3. 处理 streets.json
        print("正在处理 streets.json...")
        streets_by_city = defaultdict(list)
        with open(streets_file, 'r', encoding='utf-8') as f:
            streets_list = json.load(f)
            for street in streets_list:
                city_code = street.get('cityCode')
                if city_code:
                    street_code = street.get('code')
                    streets_by_city[city_code].append({
                        "code": street_code,
                        "name": street.get('name'),
                        "areaCode": street.get('areaCode'),
                        "villages": villages_by_street.get(street_code, [])
                    })
        print(f"处理完成，找到 {len(streets_list)} 个街道，归属于 {len(streets_by_city)} 个城市。")

        # 4. 按省份和城市生成文件结构 - areas/省文件夹/市json
        print("正在生成文件结构...")
        for province in provinces_data:
            province_code = province['code']
            province_name = province['name']
            
            # 创建省份文件夹（不带编码前缀）
            province_path = os.path.join(output_dir, province_name)
            if not os.path.exists(province_path):
                os.makedirs(province_path)
            
            # 查找属于该省份的城市
            province_cities = [c for c in cities_data if c['provinceCode'] == province_code]
            
            if not province_cities:
                print(f"警告：省份 {province_name} ({province_code}) 没有找到任何城市。")
                continue

            for city in province_cities:
                city_code = city['code']
                city_name = city['name']

                # 准备要写入的城市数据
                city_output_data = {
                    "cityCode": city_code,
                    "cityName": city_name,
                    "provinceCode": province_code,
                    "provinceName": province_name,
                    "streets": streets_by_city.get(city_code, [])
                }

                # 定义城市JSON文件名和路径（不带编码前缀）
                city_filename = f"{city_name}.json"
                city_filepath = os.path.join(province_path, city_filename)
                
                # 写入JSON文件
                with open(city_filepath, 'w', encoding='utf-8') as f:
                    json.dump(city_output_data, f, ensure_ascii=False, indent=2)
            
            print(f"已处理省份: {province_name} ({len(province_cities)} 个城市)")

        # 5. 生成轻量级的省市区三级菜单JSON
        print("\n正在生成省市区三级菜单JSON...")
        menu_data = []
        
        for province in provinces_data:
            province_code = province['code']
            province_name = province['name']
            
            # 查找属于该省份的城市
            province_cities = [c for c in cities_data if c['provinceCode'] == province_code]
            
            cities_menu = []
            for city in province_cities:
                city_code = city['code']
                city_name = city['name']
                
                # 查找属于该城市的区县
                city_areas = [a for a in areas_data if a['cityCode'] == city_code]
                
                areas_menu = []
                for area in city_areas:
                    areas_menu.append({
                        "code": area['code'],
                        "name": area['name']
                    })
                
                cities_menu.append({
                    "code": city_code,
                    "name": city_name,
                    "areas": areas_menu
                })
            
            menu_data.append({
                "code": province_code,
                "name": province_name,
                "cities": cities_menu
            })
        
        # 保存省市区菜单JSON
        menu_file = 'pca.json'
        with open(menu_file, 'w', encoding='utf-8') as f:
            json.dump(menu_data, f, ensure_ascii=False, indent=2)
        
        print(f"省市区三级菜单已保存到 '{menu_file}'")

        print("\n数据结构生成完成！")
        print(f"详细数据已保存到 '{output_dir}' 目录。")
        print("文件结构：areas/省名/市名.json")
        print(f"菜单数据已保存到 '{menu_file}'")

    except FileNotFoundError as e:
        print(f"错误：找不到文件 - {e}")
    except json.JSONDecodeError as e:
        print(f"错误：解析JSON文件时出错 - {e}")
    except Exception as e:
        print(f"发生未知错误: {e}")

if __name__ == "__main__":
    generate_from_json() 