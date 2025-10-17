import streamlit as st
import graphviz
from collections import deque
from typing import Set, Dict, List, Tuple, Any
import time

class NFA:
    """Недетерминированный конечный автомат"""
    
    def __init__(self, states: Set[int], alphabet: Set[str], 
                 transitions: Dict[int, Dict[str, List[int]]], 
                 start: int, final: Set[int]):
        self.states = states
        self.alphabet = alphabet
        self.transitions = transitions
        self.start = start
        self.final = final
    
    def epsilon_closure(self, states: Set[int]) -> Set[int]:
        """Эпсилон-замыкание множества состояний"""
        closure = set(states)
        stack = list(states)
        
        while stack:
            state = stack.pop()
            # Проверяем эпсилон-переходы (если они есть)
            if state in self.transitions and '' in self.transitions[state]:
                for next_state in self.transitions[state]['']:
                    if next_state not in closure:
                        closure.add(next_state)
                        stack.append(next_state)
        return closure
    
    def delta(self, state: int, symbol: str) -> Set[int]:
        """Функция переходов НКА"""
        if state in self.transitions and symbol in self.transitions[state]:
            return set(self.transitions[state][symbol])
        return set()
    
    def move(self, states: Set[int], symbol: str) -> Set[int]:
        """Переход из множества состояний по символу"""
        result = set()
        for state in states:
            result.update(self.delta(state, symbol))
        return result
    
    def accepts(self, word: str) -> bool:
        """Проверка, допускает ли НКА слово"""
        current_states = self.epsilon_closure({self.start})
        
        for char in word:
            if char not in self.alphabet:
                return False
            
            next_states = self.move(current_states, char)
            current_states = self.epsilon_closure(next_states)
            
            if not current_states:
                return False
        
        return bool(current_states & self.final)

class DFA:
    """Детерминированный конечный автомат"""
    
    def __init__(self, states: Set[frozenset], alphabet: Set[str],
                 transitions: Dict[frozenset, Dict[str, frozenset]],
                 start: frozenset, final: Set[frozenset]):
        self.states = states
        self.alphabet = alphabet
        self.transitions = transitions
        self.start = start
        self.final = final
    
    def accepts(self, word: str) -> Tuple[bool, List[frozenset]]:
        """Проверка, допускает ли ДКА слово. Возвращает результат и трассировку"""
        state = self.start
        trace = [state]
        
        for char in word:
            if char not in self.alphabet:
                return False, trace
            
            if state not in self.transitions or char not in self.transitions[state]:
                return False, trace
            
            state = self.transitions[state][char]
            trace.append(state)
        
        return state in self.final, trace

def thompson_algorithm_visual(nfa: NFA) -> Tuple[DFA, List[Dict[str, Any]]]:
    """
    Алгоритм Томпсона с визуализацией шагов
    """
    steps = []
    
    # Очередь для обхода в ширину
    queue = deque()
    processed = set()
    
    # Стартовое состояние ДКА
    start_dfa = frozenset([nfa.start])
    queue.append(start_dfa)
    processed.add(start_dfa)
    
    dfa_transitions = {}
    dfa_states = {start_dfa}
    
    step_count = 0
    
    while queue:
        step_count += 1
        current_state = queue.popleft()
        
        # Сохраняем информацию о шаге
        step_info = {
            'step': step_count,
            'current_state': current_state,
            'queue': list(queue.copy()),
            'processed': processed.copy(),
            'transitions': {}
        }
        
        dfa_transitions[current_state] = {}
        
        # Для каждого символа алфавита
        for symbol in nfa.alphabet:
            # Вычисляем объединение переходов из всех состояний текущего множества
            next_state = set()
            for state in current_state:
                next_state.update(nfa.delta(state, symbol))
            
            next_state_frozen = frozenset(next_state)
            dfa_transitions[current_state][symbol] = next_state_frozen
            
            step_info['transitions'][symbol] = {
                'from_state': current_state,
                'to_state': next_state_frozen,
                'is_new': next_state_frozen not in processed and bool(next_state),
                'is_empty': not bool(next_state)
            }
            
            # Если это новое состояние и оно не пустое, добавляем в очередь
            if next_state_frozen not in processed and next_state:
                queue.append(next_state_frozen)
                processed.add(next_state_frozen)
                dfa_states.add(next_state_frozen)
        
        steps.append(step_info)
    
    # Определяем конечные состояния ДКА
    dfa_final = set()
    for state in dfa_states:
        if state & nfa.final:
            dfa_final.add(state)
    
    return DFA(dfa_states, nfa.alphabet, dfa_transitions, start_dfa, dfa_final), steps

def draw_nfa(nfa: NFA) -> graphviz.Digraph:
    """Визуализация НКА"""
    dot = graphviz.Digraph('NFA')
    dot.attr(rankdir='LR')
    
    # Добавляем состояния
    for state in nfa.states:
        if state in nfa.final:
            dot.node(str(state), shape='doublecircle')
        else:
            dot.node(str(state))
        
        if state == nfa.start:
            dot.node('start', shape='point')
            dot.edge('start', str(state))
    
    # Добавляем переходы
    for from_state, transitions in nfa.transitions.items():
        for symbol, to_states in transitions.items():
            for to_state in to_states:
                dot.edge(str(from_state), str(to_state), label=symbol)
    
    return dot

def draw_dfa(dfa: DFA) -> graphviz.Digraph:
    """Визуализация ДКА"""
    dot = graphviz.Digraph('DFA')
    dot.attr(rankdir='LR')
    
    # Создаем удобные имена для состояний
    state_names = {}
    state_counter = 0
    for state in sorted(dfa.states, key=lambda s: (len(s), sorted(s))):
        if state == dfa.start:
            state_names[state] = f"q0"
        else:
            state_counter += 1
            state_names[state] = f"q{state_counter}"
    
    # Добавляем состояния
    for state in dfa.states:
        label = state_names[state]
        if state in dfa.final:
            dot.node(label, shape='doublecircle')
        else:
            dot.node(label)
        
        if state == dfa.start:
            dot.node(f'start_{label}', shape='point')
            dot.edge(f'start_{label}', label)
    
    # Добавляем переходы
    for from_state, transitions in dfa.transitions.items():
        for symbol, to_state in transitions.items():
            from_label = state_names[from_state]
            to_label = state_names[to_state]
            dot.edge(from_label, to_label, label=symbol)
    
    return dot

def main():
    st.set_page_config(page_title="НКА в ДКА визуализатор", layout="wide")
    
    st.title("🎯 Интерактивный визуализатор преобразования НКА в ДКА")
    st.subheader("Лабораторная работа №4 • Алгоритм Томпсона • Вариант 42")
    
    # Создаем боковую панель для настройки
    with st.sidebar:
        st.header("⚙️ Настройки")
        
        st.subheader("Исходный НКА №4")
        st.write("""
        **Язык**: слова, где за 3 символа до конца есть 'a'
        
        **Состояния**: {1, 2, 3, 4}  
        **Алфавит**: {a, b}  
        **Начальное**: 1  
        **Конечное**: 4
        """)
        
        st.subheader("Тестирование")
        test_word_input = st.text_input("Слово для тестирования", "aaa")
        
        st.subheader("Визуализация")
        show_steps = st.checkbox("Показывать пошаговое преобразование", True)
        animation_speed = st.slider("Скорость анимации (сек)", 0.5, 3.0, 1.0)
    
    # Определяем НКА №4
    nfa_states = {1, 2, 3, 4}
    nfa_alphabet = {'a', 'b'}
    nfa_transitions = {
        1: {'a': [1, 2], 'b': [1]},
        2: {'a': [3], 'b': [3]},
        3: {'a': [4], 'b': [4]},
        4: {'a': [], 'b': []}
    }
    nfa_start = 1
    nfa_final = {4}
    
    nfa = NFA(nfa_states, nfa_alphabet, nfa_transitions, nfa_start, nfa_final)
    
    # Основной интерфейс
    col1, col2 = st.columns(2)
    
    with col1:
        st.header("🔷 Исходный НКА")
        
        # Визуализация НКА
        st.subheader("Граф НКА")
        nfa_graph = draw_nfa(nfa)
        st.graphviz_chart(nfa_graph)
        
        # Таблица переходов НКА
        st.subheader("Таблица переходов НКА")
        nfa_table_data = []
        for state in sorted(nfa.states):
            row = {"Состояние": f"q{state}"}
            if state == nfa.start:
                row["Состояние"] = f"→ q{state}"
            if state in nfa.final:
                row["Состояние"] = f"q{state}*"
                
            for symbol in sorted(nfa.alphabet):
                if state in nfa.transitions and symbol in nfa.transitions[state]:
                    row[symbol] = "{" + ", ".join(map(str, nfa.transitions[state][symbol])) + "}"
                else:
                    row[symbol] = "∅"
            nfa_table_data.append(row)
        
        st.table(nfa_table_data)
    
    with col2:
        st.header("🔶 Результирующий ДКА")
        
        # Преобразование НКА в ДКА
        dfa, steps = thompson_algorithm_visual(nfa)
        
        # Визуализация ДКА
        st.subheader("Граф ДКА")
        dfa_graph = draw_dfa(dfa)
        st.graphviz_chart(dfa_graph)
        
        # Таблица переходов ДКА
        st.subheader("Таблица переходов ДКА")
        
        # Создаем удобные имена для состояний ДКА
        state_mapping = {}
        state_counter = 0
        for state in sorted(dfa.states, key=lambda s: (len(s), sorted(s))):
            if state == dfa.start:
                state_mapping[state] = "q0"
            else:
                state_counter += 1
                state_mapping[state] = f"q{state_counter}"
        
        dfa_table_data = []
        for state in sorted(dfa.states, key=lambda s: (len(s), sorted(s))):
            row = {"Состояние ДКА": state_mapping[state], "Множество НКА": str(set(state))}
            
            if state == dfa.start:
                row["Состояние ДКА"] = f"→ {state_mapping[state]}"
            if state in dfa.final:
                row["Состояние ДКА"] = f"{state_mapping[state]}*"
                
            for symbol in sorted(dfa.alphabet):
                if state in dfa.transitions and symbol in dfa.transitions[state]:
                    next_state = dfa.transitions[state][symbol]
                    row[symbol] = state_mapping[next_state]
                else:
                    row[symbol] = "∅"
            dfa_table_data.append(row)
        
        st.table(dfa_table_data)
    
    # Пошаговое преобразование
    if show_steps:
        st.header("📊 Пошаговое преобразование НКА → ДКА")
        
        step_container = st.container()
        with step_container:
            for i, step in enumerate(steps):
                with st.expander(f"Шаг {step['step']}: Обрабатываем состояние {set(step['current_state'])}", expanded=i==0):
                    col_a, col_b, col_c = st.columns(3)
                    
                    with col_a:
                        st.write("**Текущее состояние:**")
                        st.info(f"{{ {', '.join(map(str, sorted(step['current_state'])))} }}")
                    
                    with col_b:
                        st.write("**Очередь:**")
                        queue_states = [f"{{ {', '.join(map(str, sorted(state)))} }}" for state in step['queue']]
                        if queue_states:
                            st.write(" • " + "\n • ".join(queue_states))
                        else:
                            st.write("(пусто)")
                    
                    with col_c:
                        st.write("**Обработанные:**")
                        processed_states = [f"{{ {', '.join(map(str, sorted(state)))} }}" for state in step['processed']]
                        st.write(" • " + "\n • ".join(processed_states))
                    
                    st.write("**Переходы:**")
                    for symbol in sorted(nfa.alphabet):
                        trans_info = step['transitions'][symbol]
                        from_set = set(trans_info['from_state'])
                        to_set = set(trans_info['to_state'])
                        
                        if to_set:
                            status = "🆕 Новое" if trans_info['is_new'] else "✅ Обработано"
                            st.write(f"δ({from_set}, '{symbol}') = {to_set} **{status}**")
                        else:
                            st.write(f"δ({from_set}, '{symbol}') = ∅")
                    
                    time.sleep(animation_speed)
    
    # Тестирование слов
    st.header("🧪 Тестирование автоматов")
    
    test_col1, test_col2 = st.columns(2)
    
    with test_col1:
        st.subheader("Тестирование на НКА")
        nfa_result = nfa.accepts(test_word_input)
        st.write(f"Слово: `{test_word_input}`")
        if nfa_result:
            st.success(f"✅ НКА ПРИНИМАЕТ слово")
        else:
            st.error(f"❌ НКА ОТВЕРГАЕТ слово")
    
    with test_col2:
        st.subheader("Тестирование на ДКА")
        dfa_result, trace = dfa.accepts(test_word_input)
        st.write(f"Слово: `{test_word_input}`")
        
        if dfa_result:
            st.success(f"✅ ДКА ПРИНИМАЕТ слово")
        else:
            st.error(f"❌ ДКА ОТВЕРГАЕТ слово")
        
        st.write("**Трассировка:**")
        trace_steps = []
        for i, state in enumerate(trace):
            if i == 0:
                trace_steps.append(f"Начало: {state_mapping[state]}")
            else:
                trace_steps.append(f"После '{test_word_input[i-1]}': {state_mapping[state]}")
        
        for step in trace_steps:
            st.write(f"• {step}")
    
    # Информация о языке
    st.header("📚 Информация о языке")
    
    info_col1, info_col2 = st.columns(2)
    
    with info_col1:
        st.subheader("Регулярное выражение")
        st.code("(a|b)*a(a|b)(a|b)", language="regexp")
        st.write("""
        **Объяснение:**
        - `(a|b)*` - любая последовательность символов a и b
        - `a` - обязательный символ 'a' за 3 позиции до конца
        - `(a|b)` - любой символ на 2-й позиции с конца
        - `(a|b)` - любой символ на последней позиции
        """)
    
    with info_col2:
        st.subheader("Статистика преобразования")
        st.metric("Состояния НКА", len(nfa.states))
        st.metric("Состояния ДКА", len(dfa.states))
        st.metric("Максимум возможных состояний", 2**len(nfa.states))
        
        efficiency = len(dfa.states) / (2**len(nfa.states)) * 100
        st.metric("Эффективность", f"{efficiency:.1f}%")
        
        st.write("**Примеры слов:**")
        st.write("✅ Принимаются: `aaa`, `aba`, `aabbb`, `abab`, `aaaa`")
        st.write("❌ Отвергаются: `bbb`, `ab`, `bbab`")

if __name__ == "__main__":
    main()