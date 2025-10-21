import random
import re
import sys
from fractions import Fraction
from functools import lru_cache


# 生成数字（自然数或分数）
def generate_number(range_limit, is_fraction=False):
    if is_fraction or random.random() < 0.3:
        denominator = random.randint(2, range_limit - 1)
        numerator = random.randint(1, denominator - 1)

        if random.random() < 0.1:  # 带整数部分的分数
            integer_part = random.randint(1, range_limit - 1)
            value = integer_part + Fraction(numerator, denominator)
            return f"{integer_part}'{numerator}/{denominator}", value
        else:  # 真分数
            frac = Fraction(numerator, denominator)
            return f"{numerator}/{denominator}", frac
    else:  # 自然数
        num = random.randint(0, range_limit - 1)
        return str(num), Fraction(num)


# 规范化表达式（处理交换律去重）
def tokenize_expression(expr):
    """将表达式转换为便于处理的标记列表"""
    expr = expr.replace('(', '').replace(')', '').strip(' =')
    return re.findall(r"\d+'\d+/\d+|\d+/\d+|\d+|[+×]", expr)


def normalize_expression(expr):
    """修改：仅对最外层的+和×进行交换律去重，不递归子表达式，减少重复判定"""
    tokens = tokenize_expression(expr)
    # 只处理最外层的第一个可交换运算符
    for i in range(len(tokens)):
        if tokens[i] in ('+', '×'):
            left = tokens[:i]
            right = tokens[i+1:]
            if not left or not right:
                continue  # 跳过不完整的表达式
            left_str = ' '.join(left)
            right_str = ' '.join(right)
            if left_str > right_str:
                return ' '.join(right + [tokens[i]] + left)
    return ' '.join(tokens)


# 生成有效的表达式
def generate_valid_expression(range_limit):
    operators = [
        ('+', lambda a, b: a + b),
        ('-', lambda a, b: a - b if a >= b else None),
        ('×', lambda a, b: a * b),
        ('÷', lambda a, b: a / b if b != 0 and (a / b).denominator <= range_limit - 1 else None)
    ]

    # 增加候选数量，提高多样性
    op_count = random.randint(1, 3)
    candidates_needed = 5 + op_count  # 修改：从2+op_count增加到5+op_count

    for _ in range(candidates_needed):
        expressions = []
        values = []

        # 初始化第一个数字
        expr1, val1 = generate_number(range_limit)
        expressions.append(expr1)
        values.append(val1)

        # 逐步添加操作符和数字
        valid = True
        for _ in range(op_count):
            op_str, op_func = random.choice(operators)
            expr2, val2 = generate_number(range_limit)

            result = op_func(values[-1], val2)
            if result is None:  # 无效操作，尝试替换为加法
                op_str = '+'
                result = values[-1] + val2

            expressions.append(op_str)
            expressions.append(expr2)
            values.append(result)

        # 添加括号（增加随机性）
        full_expr = ' '.join(expressions)
        if op_count >= 2 and random.random() < 0.5:  # 修改：括号概率从30%提高到50%
            # 随机选择括号位置，不固定在前三个元素
            bracket_start = random.randint(0, len(expressions)-3)
            if bracket_start % 2 == 0:  # 确保从数字开始
                full_expr = (f"({expressions[bracket_start]} {expressions[bracket_start+1]} {expressions[bracket_start+2]}) "
                             f"{' '.join(expressions[bracket_start+3:])}")

        yield (full_expr + " =", format_result(values[-1]))


# 格式化结果为可读性高的分数
def format_result(fraction):
    if fraction.denominator == 1:
        return str(fraction.numerator)
    elif abs(fraction.numerator) > fraction.denominator:
        integer_part = fraction.numerator // fraction.denominator
        numerator = abs(fraction.numerator) % fraction.denominator
        return f"{integer_part}'{numerator}/{fraction.denominator}"
    else:
        return f"{fraction.numerator}/{fraction.denominator}"


# 生成练习题
def generate_exercises(num=10, range_limit=10):
    exercises = []
    answers = []
    seen = set()
    print(f"正在生成 {num} 道题...")

    # 增加最大尝试次数，避免提前退出
    max_attempts = num * 10  # 修改：增加尝试次数
    attempts = 0

    while len(exercises) < num and attempts < max_attempts:
        attempts += 1
        # 生成候选表达式
        for expr, ans in generate_valid_expression(range_limit):
            normalized = normalize_expression(expr)
            if normalized not in seen:
                seen.add(normalized)
                exercises.append(expr)
                answers.append(ans)

                # 进度提示
                if len(exercises) % 100 == 0:
                    print(f"已生成第 {len(exercises)} 道题")
                break

        # 防止无限循环
        if len(exercises) == len(seen) and len(exercises) < num and attempts >= max_attempts:
            print(f"警告：无法生成更多不重复的题目（当前 {len(exercises)} 道），请增大数值范围")
            break

    # 保存结果
    with open('Exercises.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(exercises))
    with open('Answers.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(answers))

    print(f"\n生成完成！共生成 {len(exercises)} 道题（目标 {num} 道）")


# 解析分数字符串为Fraction对象
@lru_cache(maxsize=None)
def parse_fraction(s):
    if "'" in s:
        integer_part, frac_part = s.split("'")
        numerator, denominator = frac_part.split("/")
        return Fraction(int(integer_part)) + Fraction(int(numerator), int(denominator))
    elif "/" in s:
        numerator, denominator = s.split("/")
        return Fraction(int(numerator), int(denominator))
    else:
        return Fraction(int(s))


# 计算表达式结果
def evaluate_expression(expr):
    try:
        # 替换运算符并解析 tokens
        expr = expr.replace('×', '*').replace('÷', '/')
        tokens = re.findall(r"\d+'\d+/\d+|\d+/\d+|\d+|[+\-*/()]", expr)

        # 转换为可计算的 Fraction 表达式
        parsed = []
        for token in tokens:
            if token in '()+*-/':
                parsed.append(token)
            else:
                frac = parse_fraction(token)
                parsed.append(f"Fraction({frac.numerator}, {frac.denominator})")

        # 计算并格式化结果
        result = eval(' '.join(parsed))
        return format_result(result)
    except Exception as e:
        print(f"计算表达式错误: {expr} -> {e}")
        return None


# 批改练习
def grade_exercises(exercise_file, answer_file):
    try:
        with open(exercise_file, 'r', encoding='utf-8') as f:
            exercises = [line.strip().rstrip('=') for line in f if line.strip()]
    except FileNotFoundError:
        print(f"错误：未找到题目文件 {exercise_file}")
        return

    try:
        with open(answer_file, 'r', encoding='utf-8') as f:
            user_answers = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"错误：未找到答案文件 {answer_file}")
        return

    if len(exercises) != len(user_answers):
        print(f"错误：题目数量（{len(exercises)}）与答案数量（{len(user_answers)}）不一致")
        return

    correct = []
    wrong = []
    for i in range(len(exercises)):
        expr = exercises[i].strip()
        user_ans = user_answers[i].strip()
        correct_ans = evaluate_expression(expr)

        if correct_ans is None:
            print(f"题目 {i + 1} 解析错误: {expr}")
            continue

        if correct_ans == user_ans:
            correct.append(i + 1)
        else:
            wrong.append(i + 1)

    # 保存批改结果
    with open('Grade.txt', 'w', encoding='utf-8') as f:
        f.write(f"Correct: {len(correct)} ({', '.join(map(str, correct))})\n")
        f.write(f"Wrong: {len(wrong)} ({', '.join(map(str, wrong))})\n")

    print("\n批改完成！结果已保存到 Grade.txt")


# 帮助信息
def print_help():
    print("用法:")
    print("生成题目: python Myapp.py -n <题目数量> -r <数值范围>")
    print("批改题目: python Myapp.py -e <exercisefile>.txt -a <answerfile>.txt")
    print("性能分析: python Myapp.py --profile")


# 主函数
def main():
    args = sys.argv[1:]

    # 处理生成题目
    if '-n' in args and '-r' in args:
        try:
            n = int(args[args.index('-n') + 1])
            r = int(args[args.index('-r') + 1])
            if n <= 0 or r < 2:  # 范围至少为2才能生成分数
                print("错误：题目数量必须为正整数，范围需≥2")
                return
            generate_exercises(n, r)
        except (IndexError, ValueError):
            print("错误：-n 和 -r 需后跟有效的整数")
            print_help()

    # 处理批改题目
    elif '-e' in args and '-a' in args:
        try:
            e_file = args[args.index('-e') + 1]
            a_file = args[args.index('-a') + 1]
            grade_exercises(e_file, a_file)
        except IndexError:
            print("错误：-e 和 -a 需后跟文件名")
            print_help()

    # 未知参数
    else:
        print("错误：参数不完整或格式错误")
        print_help()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--profile":
        import cProfile

        cProfile.run("generate_exercises(100, 100)", "profile_stats")
        print("性能数据已保存到 profile_stats，可运行 snakeviz profile_stats 查看")
    else:
        main()