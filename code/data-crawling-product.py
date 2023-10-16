# 제품 상세페이지 데이터 크롤링
import requests
import boto3
from bs4 import BeautifulSoup
from typing import List
from botocore.exceptions import ClientError

# AWS 리전과 AWS 계정 ID를 설정합니다.
aws_region = 'ap-northeast-2'
aws_access_key = '__access_key__'
aws_secret_key = '__secret_key__'


class Item:
    idx: str
    name: str
    cate: str
    img: str
    content: str
    size: int
    where: str

    n_size: int
    calories: int
    carb_sugar: int
    protein: int
    fat: int
    sat_fat: int
    trans_fat: int
    cholesterol: int
    sodium: int

    def to_dict(self):
        tmp_dict = {}
        for k in self.__dict__.keys():
            tmp_dict.update({k: {'S': self.__dict__.get(k, '')}})
        return tmp_dict


class DynamoDb:
    def __init__(self, table_name, key):
        self.table_name = table_name
        self.key = key
        self.dynamodb = boto3.client('dynamodb',
                                     region_name=aws_region,
                                     aws_access_key_id=aws_access_key,
                                     aws_secret_access_key=aws_secret_key)

    def create_table(self):
        try:
            self.dynamodb.create_table(
                TableName=self.table_name,
                KeySchema=[
                    {
                        'AttributeName': self.key,
                        'KeyType': 'HASH'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': self.key,
                        'AttributeType': 'S'
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 1,
                    'WriteCapacityUnits': 1
                }
            )
            print('table created!')
        except Exception as e:
            print(str(e))

    def put_item(self, item: Item, dup_raise: bool = True):
        try:
            cond_exp = f"attribute_not_exists({self.key})" if dup_raise else ""
            response = self.dynamodb.put_item(
                TableName=self.table_name,
                Item=item.to_dict(),
                ConditionExpression=cond_exp
            )
            print("데이터가 테이블에 입력되었습니다.")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                print("이미 존재하는 키입니다.")
                return False
            else:
                raise Exception(f"데이터 입력 중 오류 발생: {e}")
        return True


def scrape_and_store_data():
    dynamo = DynamoDb('ottogi-product', key='idx')
    dynamo.create_table()
    item_list: List[Item] = []
    base_url = "https://ottogi.co.kr/product/product_view.asp?page=1&hcode=&mcode=&stxt=&orderby=NEW&idx="

    # 1부터 2560까지 숫자를 반복하며 크롤링을 시도합니다.
    for idx in range(1, 2561):
        url = base_url + str(idx)

        # 웹 페이지에 요청을 보냅니다.
        response = requests.get(url)

        # 만약 페이지가 존재하지 않으면 400 Bad Request 오류가 발생합니다.
        # 오류가 발생하지 않으면 크롤링을 진행합니다.
        if response.status_code == 400:
            print(f"페이지 {idx}가 존재하지 않습니다. 크롤링을 건너뜁니다.")
            continue
        else:
            # BeautifulSoup을 사용하여 페이지 내용을 파싱합니다.
            data_cnt = 0
            soup = BeautifulSoup(response.text, "html.parser")
            name = soup.select_one("div.tit_content h2", class_="header center titbul").text.strip()
            cate = soup.select_one("div.tit_content p").text.strip()
            img = 'https://ottogi.co.kr' + soup.select_one("div.left p img")['src']

            tables = soup.find("table", class_="bordered vtbl recipeTbl goodsTbl")
            size = tables.select_one('tr.first td p').text.strip()
            content = tables.find_all('td')[1].text.strip()
            where = tables.find_all('td')[2].text.strip()

            results = soup.find("table", class_="bordered vtbl nutrientTbl")
            second_tr = results.find_all('tr')[1]

            n_size = (second_tr.find('th')).get_text(strip=True)
            td_elements = second_tr.find_all('td')

            # tr 내의 모든 td 값을 추출합니다.
            td_values = [td.get_text(strip=True) for td in td_elements]

            print(idx)
            print('제품명: ', name)
            print('카테고리: ', cate)
            print('이미지: ', img)
            print('총 내용량: ', size)
            print('내용: ', content)
            print('원산지: ', where)
            print('기준: ', n_size)
            print('열량: ', td_values[0])
            print('탄수화물: ', td_values[1])
            print('당류: ', td_values[2])
            print('단백질: ', td_values[3])
            print('지방: ', td_values[4])
            print('포화지방: ', td_values[5])
            print('트랜스지방: ', td_values[6])
            print('콜레스테롤: ', td_values[7])
            print('나트륨: ', td_values[8])
            print('------------------------------------------')

            item: Item = Item()
            item.idx = str(idx)
            item.name = str(name)
            item.category = str(cate)
            item.img = str(img)
            item.size = str(size)
            item.content = str(content)
            item.where = str(where)

            item.n_size = n_size
            item.calories = td_values[0]
            item.carb = td_values[1]
            item.sugar = td_values[2]
            item.protein = td_values[3]
            item.fat = td_values[4]
            item.sat_fat = td_values[5]
            item.trans_fat = td_values[6]
            item.cholesterol = td_values[7]
            item.sodium = td_values[8]
            item_list.append(item)
            succ = dynamo.put_item(item, dup_raise=True)

            if not succ:
                print('이전에 입력했던 데이터까지 넣었음. 종료!')


if __name__ == "__main__":
    # 로컬 테스트용 코드를 실행합니다.
    scrape_and_store_data()
