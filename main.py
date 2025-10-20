import random
import re
import sys
from fractions import Fraction


def generate_number(range_limit, is_fraction=False):
    """生成自然数或真分数（带分数概率低）"""
    if is_fraction or random.random() < 0.3:  # 30%概率生成分数
        denominator = random.randint(2, range_limit - 1)
        numerator = random.randint(1, denominator - 1)

        # 10%概率生成带分数
        if random.random() < 0.1:
            integer_part = random.randint(1, range_limit - 1)
            return f"{integer_part}'{numerator}/{denominator}", Fraction(integer_part) + Fraction(numerator,
                                                                                                  denominator)
        else:
            return f"{numerator}/{denominator}", Fraction(numerator, denominator)
    else:  # 自然数
        num = random.randint(0, range_limit - 1)
        return str(num), Fraction(num)


def format_result(fraction):
    """格式化计算结果为指定格式"""
    if fraction.denominator == 1:
        return str(fraction.numerator)
    elif abs(fraction.numerator) > fraction.denominator:
        integer_part = fraction.numerator // fraction.denominator
        numerator = abs(fraction.numerator) % fraction.denominator
        return f"{integer_part}'{numerator}/{fraction.denominator}"
    else:
        return f"{fraction.numerator}/{fraction.denominator}"


def generate_valid_expression(range_limit):
    """生成一个有效的表达式（最多3个运算符）"""
    operators = [('+', lambda a, b: a + b),
                 ('-', lambda a, b: a - b if a >= b else None),
                 ('×', lambda a, b: a * b),
                 ('÷', lambda a, b: a / b if b != 0 and (a / b).denominator <= range_limit - 1 else None)]

    op_count = random.randint(1, 3)  # 最多3个运算符
    expressions = []
    values = []

    expr1, val1 = generate_number(range_limit)
    expressions.append(expr1)
    values.append(val1)

    for _ in range(op_count):
        op_str, op_func = random.choice(operators)
        expr2, val2 = generate_number(range_limit)

        result = op_func(values[-1], val2)
        if result is not None:
            expressions.append(op_str)
            expressions.append(expr2)
            values.append(result)
        else:
            expressions.append('+')
            expressions.append(expr2)
            values.append(values[-1] + val2)

    full_expr = ' '.join(expressions)
    if op_count >= 2 and random.random() < 0.3:
        full_expr = f"({expressions[0]} {expressions[1]} {expressions[2]}) {' '.join(expressions[3:])}"

    return full_expr + " =", format_result(values[-1])


def generate_exercises(num=10, range_limit=10):
    """生成指定数量的题目并保存到文件"""
    exercises = []
    answers = []
    seen = set()

    print(f"正在生成 {num} 道题...")
    for i in range(num):
        while True:
            expr, ans = generate_valid_expression(range_limit)
            normalized = normalize_expression(expr)
            if normalized not in seen:
                seen.add(normalized)
                break

        exercises.append(expr)
        answers.append(ans)
        if (i + 1) % 1000 == 0:
            print(f"已生成 {i + 1} 道题")

    with open('Exercises.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(exercises))
    with open('Answers.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(answers))

    print(f"\n生成完成！共生成 {num} 道题")
    print("题目：Exercises.txt")
    print("答案：Answers.txt")


def normalize_expression(expr):
    """处理+和×的交换律，确保题目不重复"""
    expr = expr.replace('(', '').replace(')', '').strip(' =')
    tokens = expr.split()

    i = 0
    while i < len(tokens):
        if tokens[i] in ['+', '×']:
            left = ' '.join(tokens[:i])
            right = ' '.join(tokens[i + 1:])

            left_norm = normalize_expression(left)
            right_norm = normalize_expression(right)

            if left_norm > right_norm:
                left_norm, right_norm = right_norm, left_norm

            tokens = left_norm.split() + [tokens[i]] + right_norm.split()
            i = 0
        else:
            i += 1
    return ' '.join(tokens)


def parse_fraction(s):
    """解析分数字符串为Fraction对象"""
    if "'" in s:
        integer_part, frac_part = s.split("'")
        numerator, denominator = frac_part.split("/")
        return Fraction(int(integer_part)) + Fraction(int(numerator), int(denominator))
    elif "/" in s:
        numerator, denominator = s.split("/")
        return Fraction(int(numerator), int(denominator))
    else:
        return Fraction(int(s))


def evaluate_expression(expr):
    """计算表达式的值"""
    try:
        expr = expr.replace('×', '*').replace('÷', '/')
        tokens = re.findall(r"\d+'\d+/\d+|\d+/\d+|\d+|[+\-*/()]", expr)
        parsed = []
        for token in tokens:
            if token in '()+*-/':
                parsed.append(token)
            else:
                frac = parse_fraction(token)
                parsed.append(f"Fraction({frac.numerator}, {frac.denominator})")
        result = eval(' '.join(parsed))
        return format_result(result)
    except Exception as e:
        print(f"计算表达式错误: {expr} -> {e}")
        return None


def grade_exercises(exercise_file, answer_file):
    """批改题目并生成Grade.txt"""
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

    with open('Grade.txt', 'w', encoding='utf-8') as f:
        correct_str = f"Correct: {len(correct)} ({', '.join(map(str, correct))})" if correct else "Correct: 0"
        wrong_str = f"Wrong: {len(wrong)} ({', '.join(map(str, wrong))})" if wrong else "Wrong: 0"
        f.write(correct_str + '\n')
        f.write(wrong_str + '\n')

    print("\n批改完成！")
    print("统计结果已保存到 Grade.txt")
    print(correct_str)
    print(wrong_str)


def print_help():
    """打印帮助信息（适配Python运行方式）"""
    print("用法:")
    print("生成题目: python Myapp.py -n <题目数量> -r <数值范围>")
    print("批改题目: python Myapp.py -e <exercisefile>.txt -a <answerfile>.txt")
    print("说明:")
    print("  -n: 控制生成题目的个数（必填）")
    print("  -r: 控制数值范围（自然数、分数分母，必填，必须≥1）")
    print("  -e: 指定题目文件（批改时必填）")
    print("  -a: 指定答案文件（批改时必填）")
    print("示例:")
    print("  python math_exercises.py -n 10 -r 10")
    print("  python math_exercises.py -e Exercises.txt -a UserAnswers.txt")


def main():
    """命令行参数处理（修复参数数量判断逻辑）"""
    args = sys.argv[1:]  # 获取除脚本名外的所有参数

    # 生成题目：必须包含 -n 和 -r，且参数总数为4（如 -n 10 -r 5）
    if len(args) == 4 and args[0] == '-n' and args[2] == '-r':
        try:
            num = int(args[1])
            range_limit = int(args[3])
            if num <= 0:
                print("错误：题目数量必须为正整数")
                print_help()
                return
            if range_limit < 1:
                print("错误：数值范围必须≥1")
                print_help()
                return
            generate_exercises(num, range_limit)
        except ValueError:
            print("错误：题目数量和数值范围必须是整数")
            print_help()

    # 批改题目：必须包含 -e 和 -a，且参数总数为4（如 -e ex.txt -a ans.txt）
    elif len(args) == 4 and args[0] == '-e' and args[2] == '-a':
        exercise_file = args[1]
        answer_file = args[3]
        grade_exercises(exercise_file, answer_file)

    # 参数错误的情况
    else:
        print("错误：参数数量不正确或格式错误")
        print_help()


if __name__ == "__main__":
    main()