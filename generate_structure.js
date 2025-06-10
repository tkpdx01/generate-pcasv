const sqlite3 = require('sqlite3').verbose();
const fs = require('fs');
const path = require('path');

// 创建输出目录
const outputDir = 'output';
if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir);
}

// 打开数据库连接
const db = new sqlite3.Database('./dist/data.sqlite');

async function generateStructure() {
    try {
        // 获取所有省份
        const provinces = await new Promise((resolve, reject) => {
            db.all("SELECT * FROM province ORDER BY code", (err, rows) => {
                if (err) reject(err);
                else resolve(rows);
            });
        });

        console.log(`找到 ${provinces.length} 个省份`);

        for (const province of provinces) {
            console.log(`处理省份: ${province.name} (${province.code})`);
            
            // 创建省份文件夹
            const provincePath = path.join(outputDir, `${province.code}-${province.name}`);
            if (!fs.existsSync(provincePath)) {
                fs.mkdirSync(provincePath);
            }

            // 获取该省份的所有城市
            const cities = await new Promise((resolve, reject) => {
                db.all("SELECT * FROM city WHERE provinceCode = ? ORDER BY code", [province.code], (err, rows) => {
                    if (err) reject(err);
                    else resolve(rows);
                });
            });

            console.log(`  - 找到 ${cities.length} 个城市`);

            for (const city of cities) {
                console.log(`    处理城市: ${city.name} (${city.code})`);
                
                // 获取该城市的所有街道
                const streets = await new Promise((resolve, reject) => {
                    db.all(`
                        SELECT s.*, a.name as areaName 
                        FROM street s 
                        LEFT JOIN area a ON s.areaCode = a.code 
                        WHERE s.cityCode = ? 
                        ORDER BY s.code
                    `, [city.code], (err, rows) => {
                        if (err) reject(err);
                        else resolve(rows);
                    });
                });

                // 为每个街道获取村庄数据
                const streetsWithVillages = [];
                for (const street of streets) {
                    const villages = await new Promise((resolve, reject) => {
                        db.all("SELECT * FROM village WHERE streetCode = ? ORDER BY code", [street.code], (err, rows) => {
                            if (err) reject(err);
                            else resolve(rows);
                        });
                    });

                    streetsWithVillages.push({
                        code: street.code,
                        name: street.name,
                        areaCode: street.areaCode,
                        areaName: street.areaName,
                        villages: villages.map(village => ({
                            code: village.code,
                            name: village.name,
                            streetCode: village.streetCode
                        }))
                    });
                }

                // 创建城市JSON文件
                const cityData = {
                    cityCode: city.code,
                    cityName: city.name,
                    provinceCode: province.code,
                    provinceName: province.name,
                    streets: streetsWithVillages
                };

                const cityFileName = `${city.code}.json`;
                const cityFilePath = path.join(provincePath, cityFileName);
                fs.writeFileSync(cityFilePath, JSON.stringify(cityData, null, 2), 'utf8');
                
                console.log(`      - 创建文件: ${cityFileName} (${streetsWithVillages.length} 个街道)`);
            }
        }

        console.log('数据结构生成完成！');
        
    } catch (error) {
        console.error('处理过程中出错:', error);
    } finally {
        db.close();
    }
}

// 运行脚本
generateStructure(); 