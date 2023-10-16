# 레시피 데이터 크롤링
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
    tags: str
    img: str
    content: str
    ingredients: str
    recipe: str
    imgs: str

    calories: int
    total_fat: int
    sat_fat: int
    sodium: int
    carbon: int
    diet_fiber: int
    protein: int
    vit_A: int
    vit_C: int
    calcium: int
    items_name: str
    items_img: str
    items_link: str

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
    dynamo = DynamoDb('ottogi-recipe', key='idx')
    dynamo.create_table()
    item_list: List[Item] = []
    base_url = "https://ottogi.okitchen.co.kr/category/detail.asp?idx="

    # 1부터 1450까지 숫자를 반복하며 크롤링을 시도합니다.
    for idx in range(1400, 1451):
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

            error_message = "ADODB.Field"
            page_content = response.text

            if error_message in page_content:
                print(f"페이지 {idx}에서 ADODB.Field 오류가 발생하여 크롤링을 중단합니다.")
                continue
            # detailTop 클래스의 div 안에 iframe이 있는지 확인
            detail_top_div = soup.find("div", class_="detailTop")
            iframe = detail_top_div.find("iframe") if detail_top_div else None

            if iframe:
                # iframe이 있는 경우 크롤링을 멈추고 다음 페이지로 넘어감
                print(f"페이지 {idx}에 iframe이 있습니다. 크롤링을 멈추고 다음 페이지로 넘어갑니다.")
                continue
            info = soup.find("div.detailInfo")
            name = soup.select_one("div.detailInfo h2").text.strip()

            content = soup.select_one("div.detailInfo p").text.strip()

            tags_a = soup.select('div.detailInfo a')

            if tags_a:
                tags = [a_tag.text.strip() for a_tag in tags_a]
            else:
                print(f"레시피 페이지가 아닙니다. {idx}페이지 크롤링을 건너뜁니다 *^^*")
                continue

            recipe = [p_tag.text.strip() for p_tag in soup.select('div.ContentArea p')]
            ingr = soup.select_one("div.ingredients p")
            if ingr:
                ingredients = [ingr.text.strip()]
            else:
                ingredients = []
            imgs = ['https://ottogi.okitchen.co.kr/' + img['src'] for img in soup.find_all('img', class_='txc-image')]
            img = 'https://ottogi.co.kr' + soup.select_one("div.container.detailTop img")['src']

                # 영양성분 데이터가 있는지 확인
            td_table = soup.find("table", class_="tb_nutri")
            if td_table:
                # tr 내의 모든 td 값을 추출합니다.
                td_values = [td.text.strip() for td in td_table.select('td')]
                if len(td_values) <= 9 :
                    td_values = [""] * 10

            else:
                # 영양성분 데이터가 없는 경우, 빈 값으로 초기화
                td_values = [""] * 10

            items_name = [p.text.strip() for p in soup.find_all(".made-item ul.item01 li div.img a p")]
            items_img = [img['src'] for img in soup.find_all(".made-item ul.item01 li div.img a img")]
            items_link = [a['href'] for a in soup.find_all(".made-item ul.item01 li div.link a")]

            print(idx)
            print('요리명: ', name)
            print('카테고리: ', tags)
            print('이미지: ', img)
            print('내용: ', content)
            print('재료: ', ingredients)
            print('레시피: ', recipe)
            print('레시피 사진: ', imgs)
            print('열량: ', td_values[0])
            print('총 지방: ', td_values[1])
            print('포화지방: ', td_values[2])
            print('나트륨: ', td_values[3])
            print('탄수화물: ', td_values[4])
            print('식이섬유: ', td_values[5])
            print('단백질: ', td_values[6])
            print('비타민A: ', td_values[7])
            print('비타민C: ', td_values[8])
            print('칼슘: ', td_values[9])
            print('관련제품명: ', items_name)
            print('관련제품사진: ', items_img)
            print('관련제품링크: ', items_link)
            print('------------------------------------------')

            item: Item = Item()
            item.idx = str(idx)
            item.name = str(name)
            item.tags = str(tags)
            item.img = str(img)
            item.content = str(content)
            item.ingredients = str(ingredients)
            item.recipe = str(recipe)
            item.imgs = str(imgs)

            item.calories = td_values[0]
            item.total_fat = td_values[1]
            item.sat_fat = td_values[2]
            item.sodium = td_values[3]
            item.carbon = td_values[4]
            item.diet_fiber = td_values[5]
            item.protein = td_values[6]
            item.vit_A = td_values[7]
            item.vit_C = td_values[8]
            item.calcium = td_values[9]

            item.items_name = str(items_name)
            item.items_img = str(items_img)
            item.items_link = str(items_link)

            item_list.append(item)
            succ = dynamo.put_item(item, dup_raise=True)

            if not succ:
                print('이전에 입력했던 데이터까지 넣었음. 종료!')


if __name__ == "__main__":
    # 로컬 테스트용 코드를 실행합니다.
    scrape_and_store_data()
