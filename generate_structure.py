import sqlite3
import json
import os

def create_directory_structure():
    # 创建输出目录
    output_dir = 'output'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 连接数据库
    conn = sqlite3.connect('./dist/data.sqlite')
    cursor = conn.cursor()
    
    try:
        # 获取所有省份
        cursor.execute("SELECT * FROM province ORDER BY code")
        provinces = cursor.fetchall()
        
        print(f"找到 {len(provinces)} 个省份")
        
        for province in provinces:
            province_code, province_name = province
            print(f"处理省份: {province_name} ({province_code})")
            
            # 创建省份文件夹
            province_path = os.path.join(output_dir, f"{province_code}-{province_name}")
            if not os.path.exists(province_path):
                os.makedirs(province_path)
            
            # 获取该省份的所有城市
            cursor.execute("SELECT * FROM city WHERE provinceCode = ? ORDER BY code", (province_code,))
            cities = cursor.fetchall()
            
            print(f"  - 找到 {len(cities)} 个城市")
            
            for city in cities:
                city_code, city_name, city_province_code = city
                print(f"    处理城市: {city_name} ({city_code})")
                
                # 获取该城市的所有街道（包含区域信息）
                cursor.execute("""
                    SELECT s.code, s.name, s.areaCode, a.name as areaName
                    FROM street s 
                    LEFT JOIN area a ON s.areaCode = a.code 
                    WHERE s.cityCode = ? 
                    ORDER BY s.code
                """, (city_code,))
                streets = cursor.fetchall()
                
                # 为每个街道获取村庄数据
                streets_with_villages = []
                for street in streets:
                    street_code, street_name, area_code, area_name = street
                    
                    # 获取该街道的所有村庄
                    cursor.execute("SELECT * FROM village WHERE streetCode = ? ORDER BY code", (street_code,))
                    villages = cursor.fetchall()
                    
                    street_data = {
                        "code": street_code,
                        "name": street_name,
                        "areaCode": area_code,
                        "villages": []
                    }
                    
                    for village in villages:
                        village_code, village_name, village_street_code, _, _, _ = village
                        street_data["villages"].append({
                            "code": village_code,
                            "name": village_name,
                            "streetCode": village_street_code
                        })
                    
                    streets_with_villages.append(street_data)
                
                # 创建城市JSON文件
                city_data = {
                    "cityCode": city_code,
                    "cityName": city_name,
                    "provinceCode": province_code,
                    "provinceName": province_name,
                    "streets": streets_with_villages
                }
                
                city_file_name = f"{city_code}.json"
                city_file_path = os.path.join(province_path, city_file_name)
                
                with open(city_file_path, 'w', encoding='utf-8') as f:
                    json.dump(city_data, f, ensure_ascii=False, indent=2)
                
                print(f"      - 创建文件: {city_file_name} ({len(streets_with_villages)} 个街道)")
        
        print("数据结构生成完成！")
        
        # 显示一些统计信息
        print("\n统计信息:")
        cursor.execute("SELECT COUNT(*) FROM province")
        province_count = cursor.fetchone()[0]
        print(f"省份数量: {province_count}")
        
        cursor.execute("SELECT COUNT(*) FROM city")
        city_count = cursor.fetchone()[0]
        print(f"城市数量: {city_count}")
        
        cursor.execute("SELECT COUNT(*) FROM street")
        street_count = cursor.fetchone()[0]
        print(f"街道数量: {street_count}")
        
        cursor.execute("SELECT COUNT(*) FROM village")
        village_count = cursor.fetchone()[0]
        print(f"村庄数量: {village_count}")
        
        # 特别显示直辖市的处理情况
        print("\n直辖市处理:")
        direct_municipalities = ['11', '12', '31', '50']  # 北京、天津、上海、重庆
        for dm_code in direct_municipalities:
            cursor.execute("SELECT name FROM province WHERE code = ?", (dm_code,))
            province_result = cursor.fetchone()
            if province_result:
                province_name = province_result[0]
                cursor.execute("SELECT code, name FROM city WHERE provinceCode = ?", (dm_code,))
                cities_in_dm = cursor.fetchall()
                print(f"  {province_name}: {len(cities_in_dm)} 个城市级别")
                for city_code, city_name in cities_in_dm:
                    cursor.execute("SELECT COUNT(*) FROM street WHERE cityCode = ?", (city_code,))
                    street_count_in_city = cursor.fetchone()[0]
                    print(f"    - {city_name} ({city_code}): {street_count_in_city} 个街道")
        
    except Exception as e:
        print(f"处理过程中出错: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    create_directory_structure() 