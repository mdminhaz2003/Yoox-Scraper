def scraper(product_url: str, serial_number: int) -> None:
    try:
        driver.switch_to.window(driver.window_handles[serial_number % 2])
        driver.get(product_url)
        driver.implicitly_wait(2.5)

        soup = BeautifulSoup(markup=driver.page_source, features='html.parser')
        json_data_script_tag = soup.find(name="script", attrs={'id': '__NEXT_DATA__', 'type': 'application/json'})
        to_dict = json.loads(json_data_script_tag.text).get("props")["pageProps"]["initialState"]

        handle_str = to_dict.get("itemApi")['code']
        try:
            title = to_dict.get("itemApi")['title']
        except KeyError:
            title = to_dict["itemApi"]["microCategory"]["singleDescription"]

        body_html = to_dict["itemApi"]["descriptions"]["ItemDescription"]
        vendor = to_dict.get("itemApi")["brand"]["name"]
        custom_product_type = to_dict["itemApi"]["microCategory"]["singleDescription"]
        price_str = str(to_dict["itemApi"]["priceFinal"]["transactional"]["amount"]).replace(",", "")

        tags = ""
        for tag in to_dict["breadcrumbs"]:
            tags = tag["title"] if tags == "" else f"{tags}, {tag['title']}"

        available_sizes = [size['default']['text'] for size in to_dict['itemApi']['sizes']]
        available_colors = [color["name"] for color in to_dict["itemApi"]["colors"]]
        available_product_key = [color["code10"] for color in to_dict["itemApi"]["colors"]]

        sizes = []
        for size in available_sizes:
            for _ in range(len(available_colors)):
                sizes.append(size)

        colors = available_colors * len(available_sizes)
        price = [price_str for _ in colors]
        image_format_values = to_dict["itemApi"]["imagesFormatValues"]

        image_url = []
        variant_image = []
        for code10 in available_product_key:
            for format_key in image_format_values:
                if image_format_values.index(format_key) == 0:
                    variant_image.append(f"https://cdn.yoox.biz//images/items/{code10[:2]}/{code10}_14{format_key}.jpg")
                else:
                    pass
                image_url.append(f"https://cdn.yoox.biz//images/items/{code10[:2]}/{code10}_14{format_key}.jpg")

        image_position = [str(number) for number in range(1, len(image_url) + 1)]

        json_template = JsonTemplate(
            handle_text=handle_str,
            title=title,
            body_html=body_html,
            vendor=vendor,
            custom_product_type=custom_product_type,
            tags=tags,
            product_id=product_url,
            colors=colors,
            sizes=sizes,
            price=price,
            image_src=image_url,
            image_position=image_position,
            variant_image=variant_image
        )

        product_data = json_template.main_dict()

        if not db.contains(query.ID.any(query.value == str(product_url))):
            db.insert(product_data)
            url_db.remove(query.url == product_url)
            print(f"Inserted {product_url}")
        else:
            url_db.remove(query.url == product_url)
            print(f"This Product already Exists in Database {product_url}")
    except Exception as ex:
        print(ex)


if __name__ == '__main__':
    import json
    import re
    from dotenv import dotenv_values
    from bs4 import BeautifulSoup
    from tinydb import TinyDB, Query
    import undetected_chromedriver as uc
    from basic_files.base_json_template import JsonTemplate

    config = dotenv_values(dotenv_path="./.env")
    db = TinyDB("./db_files/yoox_product_info.json")
    url_db = TinyDB("./db_files/yoox_product_url.json")
    urls = url_db.all()
    query = Query()

    base_url = config['BASE_URL']
    chrome_options = uc.ChromeOptions()
    driver = uc.Chrome(
        driver_executable_path=config['DRIVER_PATH'],  # input your driver path
        options=chrome_options
    )
    driver.get(base_url)
    driver.implicitly_wait(time_to_wait=2)
    driver.switch_to.new_window(type_hint='tab')

    condition = re.compile(r"[,'/\\.()^&%$#@!~*|\"]")

    for url in urls:
        try:
            scraper(url['url'], urls.index(url))
        except Exception as e:
            print(e)

