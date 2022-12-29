import csv
import datetime
import re
import matplotlib.pyplot as plt
import pdfkit
from matplotlib.ticker import IndexLocator
from jinja2 import Environment, FileSystemLoader

class DictByCity:
    def __init__(self):
        self.dic_data = {}
        self.total_cnt = 0

    def addata(self, city, val):
        if city not in self.dic_data.keys():
            self.dic_data[city] = [val, 1]
        else:
            self.dic_data[city][0] += val
            self.dic_data[city][1] += 1
        self.total_cnt += 1

    def get_sal(self):
        sub_dic = {}
        dic_sorted = dict(sorted(self.dic_data.items(), key=lambda item: item[1][0] // item[1][1], reverse=True))
        for key, val in dic_sorted.items():
            ratio = val[1] / self.total_cnt
            if ratio >= 0.01:
                sub_dic[key] = int(val[0] // val[1])
            if len(sub_dic) == 10:
                break
        return sub_dic

    def get_cnt(self):
        sub_dic = {}
        dic_sorted = dict(sorted(self.dic_data.items(), key=lambda item: item[1][1], reverse=True))
        cnt_topcity = 0
        for key, value in dic_sorted.items():
            ratio = value[1] / self.total_cnt
            if ratio >= 0.01:
                sub_dic[key] = round(ratio, 4)
                cnt_topcity += value[1]
            if len(sub_dic) == 10:
                new_ratio = 1 - cnt_topcity / self.total_cnt
                sub_dic["Другие"] = round(new_ratio, 4)
                break
        return sub_dic

class DictByYear:
    def __init__(self):
        self.dic_data = {}

    def addata(self, year, val, cnt):
        if year not in self.dic_data.keys():
            self.dic_data[year] = [val, cnt]
        else:
            self.dic_data[year][0] += val
            self.dic_data[year][1] += cnt

    def get_sal(self):
        sub_dic = {}
        for key, val in self.dic_data.items():
            sub_dic[key] = int(val[0] // val[1]) if val[1] != 0 else 0
        return sub_dic

    def get_cnt(self):
        sub_dic = {}
        for key, val in self.dic_data.items():
            sub_dic[key] = val[1]
        return sub_dic

class DataSet:
    def __init__(self, file_name):
        self.file_name = file_name
        self.vac_obj = DataSet.set_vac(*DataSet.csv_reader(file_name))
        self.sal_cnt_year = DictByYear()
        self.sal_job_year = DictByYear()
        self.sal_cnt_city = DictByCity()

    @staticmethod
    def csv_reader(file_name):
        file_csv = csv.reader(open(file_name, encoding='utf_8_sig'))
        data_list = [x for x in file_csv if x.count('') == 0]
        return data_list[0], data_list[1:]

    @staticmethod
    def set_vac(headers, vacancies):
        vac_list = []
        for vac in vacancies:
            dict = {}
            for i, item in enumerate(headers):
                dict[item] = vac[i]
            vac_list.append(
                Vacancy(dict['name'], dict['salary_from'], dict['salary_to'], dict['salary_currency'], dict['area_name'],
                        dict['published_at']))
        return vac_list

    def collect_stat(self, prof):
        for vac in self.vac_obj:
            self.sal_cnt_year.addata(vac.published_at.year, vac.average_salary, 1)
            if prof in vac.name:
                self.sal_job_year.addata(vac.published_at.year, vac.average_salary, 1)
            else:
                self.sal_job_year.addata(vac.published_at.year, 0, 0)
            self.sal_cnt_city.addata(vac.area_name, vac.average_salary)

    def get_stat(self):
        return self.sal_cnt_year.get_sal(), \
               self.sal_cnt_year.get_cnt(), \
               self.sal_job_year.get_sal(), \
               self.sal_job_year.get_cnt(), \
               self.sal_cnt_city.get_sal(), \
               self.sal_cnt_city.get_cnt()

    def print_stat(self):
        print(f"Динамика уровня зарплат по годам: {self.sal_cnt_year.get_sal()}")
        print(f"Динамика количества вакансий по годам: {self.sal_cnt_year.get_cnt()}")
        print(
            f"Динамика уровня зарплат по годам для выбранной профессии: {self.sal_job_year.get_sal()}")
        print(
            f"Динамика количества вакансий по годам для выбранной профессии: {self.sal_job_year.get_cnt()}")
        print(f"Уровень зарплат по городам (в порядке убывания): {self.sal_cnt_city.get_sal()}")
        print(
            f"Доля вакансий по городам (в порядке убывания): {dict(list(self.sal_cnt_city.get_cnt().items())[:10])}")

class Vacancy:
    cur_rub = {
        "AZN": 35.68,
        "BYR": 23.91,
        "EUR": 59.90,
        "GEL": 21.74,
        "KGS": 0.76,
        "KZT": 0.13,
        "RUR": 1,
        "UAH": 1.64,
        "USD": 60.66,
        "UZS": 0.0055,
    }

    def __init__(self, name, salary_from, salary_to, salary_currency, area_name, published_at):
        self.name = name
        self.average_salary = (float(salary_from) + float(salary_to)) / 2 * Vacancy.cur_rub[
            salary_currency]
        self.area_name = area_name
        self.published_at = datetime.datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%S%z")


class Report:
    def __init__(self, sal_year, cnt_year, sal_job_year, job_cnt_year, sal_city, cnt_city, prof):
        self.prof = prof
        self.sal_year = sal_year
        self.cnt_year = cnt_year
        self.prof_sal_year = sal_job_year
        self.prof_cnt_year = job_cnt_year
        self.sal_city = sal_city
        self.cnt_city = cnt_city

    def generate_image(self):
        fig, ax = plt.subplots(2, 2)
        self.create_graph1(ax[0, 0])
        self.create_graph2(ax[0, 1])
        self.create_graph3(ax[1, 0])
        self.create_graph4(ax[1, 1])
        plt.tight_layout()
        plt.savefig("graph.png")
        plt.show()

    def create_graph1(self, ax):
        ax.set_title("Уровень зарплат по годам")
        with1 = 0.4
        ax.bar([val - with1 / 2 for val in range(len(self.sal_year.keys()))], self.sal_year.values(), width=with1,
               label="средняя з/п")
        ax.bar([val + with1 / 2 for val in range(len(self.sal_year.keys()))],
               self.prof_sal_year.values(), width=with1, label=f"з/п {self.prof}")
        ax.set_xticks(range(self.sal_year.__len__()), self.sal_year.keys(), rotation="vertical")
        ax.tick_params(axis="both", labelsize=8)
        ax.legend(fontsize=8)
        ax.yaxis.set_major_locator(IndexLocator(base=10000, offset=0))

    def create_graph2(self, ax):
        ax.set_title("Количество ваканский по годам")
        with2 = 0.4
        ax.bar([val - with2 / 2 for val in range(len(self.cnt_year))], self.cnt_year.values(), width=with2,
               label="Количество ваканксий")
        ax.bar([val + with2 / 2 for val in range(len(self.cnt_year))],
               self.prof_cnt_year.values(), width=with2, label=f"Количество ваканксий\n{self.prof}")
        ax.set_xticks(range(len(self.cnt_year)), self.cnt_year.keys(), rotation="vertical")
        ax.tick_params(axis="both", labelsize=8)
        ax.legend(fontsize=8, loc='upper left')

    def create_graph3(self, ax):
        ax.set_title("Уровень зарплат по городам")
        y_posith = range(len(self.sal_city))
        cities = [re.sub(r"[- ]", "\n", c) for c in self.sal_city.keys()]
        ax.barh(y_posith, self.sal_city.values())
        ax.set_yticks(y_posith, cities)
        ax.invert_yaxis()
        ax.tick_params(axis="x", labelsize=8)
        ax.tick_params(axis="y", labelsize=6)

    def create_graph4(self, ax):
        ax.set_title("Доля вакансий по городам")
        dic_sorted = dict(sorted(self.cnt_city.items(), key=lambda item: item[1], reverse=True))
        ax.pie(dic_sorted.values(), labels=dic_sorted.keys(), textprops={'fontsize': 6})

    def generate_pdf(self):
        env = Environment(loader=FileSystemLoader("."))
        template = env.get_template("pdf_template.html")

        heads_years = ["Год", "Средняя зарплата", f"Средняя зарплата - {self.prof}", "Количество вакансий",
                       f"Количество вакансий - {self.prof}"]
        heads_cities = ["Город", "Уровень зарплат", "Город", "Доля вакансий"]

        dic_formatted = dict([(k, f"{v:.2%}") for k, v in list(self.cnt_city.items())[:10]])

        pdf_template = template.render(
            {"profession": self.prof, "salary_by_year": self.sal_year, "count_by_year": self.cnt_year,
             "profession_salary_by_year": self.prof_sal_year,
             "profession_count_by_year": self.prof_cnt_year,
             "salary_by_city": self.sal_city,
             "count_by_city": dic_formatted,
             "heads_years": heads_years,
             "heads_cities": heads_cities})
        config = pdfkit.configuration(wkhtmltopdf=r'D:\Проги\wkhtmltopdf\bin\wkhtmltopdf.exe')
        pdfkit.from_string(pdf_template, 'report.pdf', configuration=config, options={"enable-local-file-access": None})


file_name = input('Введите название файла: ')
prof = input('Введите название профессии: ')
data1 = DataSet(file_name)
data1.collect_stat(prof)
data1.print_stat()

rep = Report(*data1.get_stat(), prof)
rep.generate_image()
rep.generate_pdf()
