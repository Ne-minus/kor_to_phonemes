import re
from konlpy.tag import Twitter
from konlpy.tag import Kkma
import csv
import wget
import os

class BorderMaker:

    def __init__(self):
        self.twitter = Twitter()
        self.kkma = Kkma()

        self.final_trans = dict()
        self.path_to_module = os.path.dirname(__file__)
        self.weight_path = os.path.join(self.path_to_module, "static", "final_trans.csv")
        with open(self.weight_path, 'r') as ft_file:
            spamreader = csv.reader(ft_file)

            for row in spamreader:
                self.final_trans[row[0]] = row[2]

    def intruser(self, word: str) -> str:
        ready_word = ''
        for char in word:
            ready_word += '-' + self.final_trans[char]
        return ready_word.strip('-')

    def separator(self, text: str) -> str:
        syll_dict = dict()

        with open(self.weight_path, 'r') as csvfile:
            spamreader = csv.reader(csvfile)
            sylls = list(spamreader)
            for s in sylls:
                syll_dict[s[0]] = s[2]

        good_text = ' '
        twit_morph = self.twitter.pos(text, norm=True)

        lil_morphs = ('Josa', 'Suffix', 'Eomi', 'PreEomi')
        end_morphs = ('Exclamation', 'Conjunction', 'Eomi', 'PreEomi')
        bad = ('Foreign', 'Alpha', 'Number', 'Unknown', 'KoreanParticle',
               'Hashtag', 'ScreenName', 'Email', 'URL')

        for entity in twit_morph:
            if entity[1] in lil_morphs:
                if entity[0] == '의':
                    good_text = good_text.strip(" /-#") + '-ɛ#'  # генитив
                else:
                    good_text = good_text.strip(" /-#") + '-' + self.intruser(entity[0]) + '#'

            elif entity[1] in end_morphs:
                if good_text.endswith('/ '):
                    good_text += self.intruser(entity[0]) + ' / '
                else:
                    good_text += self.intruser(entity[0]) + ' / '

            elif entity[1] == 'Adjective' or entity[1] == 'Verb':
                # отглагольные существительные должны вести себя как
                # существительные
                if entity[0].endswith('ki'):
                    good_text += self.intruser(entity[0]) + '#'
                else:
                    tr = self.intruser(entity[0])
                    if 'ɾ-ke-jo' in tr:
                        # ㄹ게요
                        rtr = ''.join(reversed(list(tr)))
                        rtr = rtr.replace('ek-ɾ', 'ek͈-ɾ', 1)
                        tr = ''.join(reversed(list(rtr)))

                    elif 'ɾ-kʌ-jɐ' in tr or 'ɾ-kʌ-je-jo' in tr:
                        # ㄹ거(예요 / 야)
                        rtr = ''.join(reversed(list(tr)))
                        rtr = rtr.replace('ʌk-ɾ', 'ʌk͈-ɾ', 1)
                        tr = ''.join(reversed(list(rtr)))

                    elif 'm-tɐ-ko' in tr or 'm-tɐ /' in tr:
                        # ㅁ다
                        rtr = ''.join(reversed(list(tr)))
                        rtr = rtr.replace('ɐt-m', 'ɐt͈-m', 1)
                        tr = ''.join(reversed(list(rtr)))

                    # проверяем, аттрибутивное или предикативное употребление
                    if 'ETD' in self.kkma.pos(entity[0])[-1][1]:
                        good_text += tr + '#'
                    else:
                        good_text += tr + ' / '
            elif entity[1] == 'Punctuation':
                good_text = good_text.strip(" /-#") + ' / '
            elif entity[1] in bad:
                pass

            else:
                good_text += self.intruser(entity[0]) + '#'

        return good_text.strip(' /#') + ' / '



class Transcription:

    def __init__(self):
        self.borders = BorderMaker()

    def exceptions(self, given):  # must be first!!
        # сюда можно записать все исключения (и ханчу и риыль тоже)

        # 덕분에
        given = given.replace('tʌk-pun-e', 't͈ʌk-pun-e')
        return given

    def palatalization(self, given):  # must be second!!
        to_pal = ['k', 'g', 'l', 'ɾ', 'm', 'p', 's', 'ŋ', 'cʰ', 'kʰ', 'tʰ', 'pʰ',
                  't', 'n', 'h', 'k͈', 't͈', 'p͈', 's͈', 'c͈']

        front_row = ['i', 'e']

        for tp in to_pal:
            # гласные переднего ряда
            for fr in front_row:
                given = given.replace(tp + '-' + fr, tp + 'ʲ-' + fr)
                given = given.replace(tp + fr, tp + 'ʲ' + fr)

            # йотированные гласные
            given = given.replace(tp + '-j', tp + 'ʲ-')

        return given

    def yi(self, given):
        # читает ый
        res = ''
        for i in range(len(given)):
            if given[i] == 'ы':
                if given[i - 1] == '/':
                    res += 'ɰi'
                else:
                    res += 'i'
            else:
                res += given[i]
        return res

    def liquids(self, given):
        vowels = ['ɐ', 'ʌ', 'o', 'ɨ', 'u', 'i', 'ɛ', 'e', 'ɰi']
        given = given.replace('ɾ', 'l')
        for v in vowels:
            given = given.replace('l' + v, 'ɾ' + v)
            given = given.replace('l-' + v, 'ɾ-' + v)
            # нечитаемое ㅎ
            given = given.replace('lh-' + v, 'ɾ-' + v)
            given = given.replace('l-h' + v, 'ɾ-' + v)
        return given

    def aspiration(self, given):

        to_fix_k = ['k-h', 'k͈-h', 'kʰ-h', 'h-k', 'h-k͈', 'h-kʰ']
        to_fix_t = ['t-h', 't͈-h', 'tʰ-h', 'h-t', 'h-t͈', 'h-tʰ']
        to_fix_c = ['c-h', 'c͈-h', 'cʰ-h', 'h-c', 'h-c͈', 'h-cʰ']
        to_fix_p = ['p-h', 'p͈-h', 'pʰ-h', 'h-p', 'h-p͈', 'h-pʰ']

        for k in to_fix_k:
            given = given.replace(k, '-kʰ')
        for t in to_fix_t:
            given = given.replace(t, '-tʰ')
        for c in to_fix_c:
            given = given.replace(c, '-cʰ')
        for p in to_fix_p:
            given = given.replace(p, '-pʰ')

        # нечитаемый ㅎ (с ㄹ разобрались в liquids)
        h_silent = ['m-h', 'n-h', 's-h', 's͈-h',
                    'h-m', 'h-n', 'h-s', 'h-s͈', 'ŋ-h']
        for h in h_silent:
            hh = h.replace('h', '')
            given = given.replace(h, hh)

        return given

    def stop_assim(self, given):
        # ассимиляция взрывных перед сонорными
        seps = ['-', '#']
        sonors = ['m', 'n']
        stops_to_sonors = {'m': ['p', 'pʰ', 'p͈', 'lb', 'ps'],
                           'n': ['t', 'tʰ', 't͈', 'c', 'cʰ', 'c͈', 's', 's͈'],
                           'ŋ': ['k', 'kʰ', 'k͈', 'lg', 'ks'],
                           }
        for s in seps:
            chunks = given.split(s)
            for i in range(len(chunks) - 1):
                for k, v in stops_to_sonors.items():
                    bgram = re.search(r'(lg|ps|ks|lb|cʰ|kʰ|tʰ|pʰ|t͈|k͈|p͈|c͈)', chunks[i][-2:])
                    if bgram is None:
                        if chunks[i][-1] in v and chunks[i + 1][0] == 'ɾ':
                            chunks[i] = chunks[i][:-1] + k
                            chunks[i + 1] = 'n' + chunks[i + 1][1:]

                        elif chunks[i][-1] in v and chunks[i + 1][0] in sonors:
                            chunks[i] = chunks[i][:-1] + k
                    else:
                        if bgram.group(1) in v and chunks[i + 1][0] == 'ɾ':
                            chunks[i] = chunks[i][:-2] + k
                            chunks[i + 1] = 'n' + chunks[i + 1][1:]

                        elif bgram.group(1) in v and chunks[i + 1][0] in sonors:
                            chunks[i] = chunks[i][:-2] + k
            given = s.join(chunks)

        return given

    def spirantization(self, given):
        seps = ['-', '#']
        for s in seps:
            chunks = given.split(s)
            for i in range(len(chunks) - 1):
                if chunks[i][-1] in ['t', 'tʰ', 't͈'] and chunks[i + 1][0] in ['s', 's͈']:
                    chunks[i] = chunks[i][:-1] + 's'

            given = s.join(chunks)

        return given

    def sonor_assim(self, given):
        # после stop_assim
        # ассимиляция сонорных ㄹ-ㄴ, ㅁ/ㄴ-ㄹ
        seps = ['-', '#']
        final_sonor = ['m', 'ŋ']
        for s in seps:
            chunks = given.split(s)
            for i in range(len(chunks) - 1):
                if chunks[i][-1] == 'ɾ' and chunks[i + 1][0] == 'n':
                    chunks[i] = chunks[i][:-1] + 'l'
                    chunks[i + 1] = 'l' + chunks[i + 1][1:]

                elif chunks[i][-1] == 'n' and chunks[i + 1][0] == 'ɾ':
                    chunks[i] = chunks[i][:-1] + 'l'
                    chunks[i + 1] = 'l' + chunks[i + 1][1:]

                elif chunks[i][-1] in final_sonor and chunks[i + 1][0] == 'ɾ':
                    chunks[i + 1] = 'n' + chunks[i + 1][1:]
            given = s.join(chunks)

        return given

    def coronal_asim(self, given):
        # ассимиляция переднеязычных

        seps = ['-', '#']
        coronals = ['t', 't͈', 'tʰ', 's', 's͈']

        labial = ['m', 'p', 'pʰ', 'p͈']
        post_alveolar = ['cʰ', 'c', 'c͈']
        velars = ['k', 'kʰ', 'k͈', 'g']
        for s in seps:
            chunks = given.split(s)
            for i in range(len(chunks) - 1):
                # before labial
                if chunks[i][-1] in coronals and chunks[i + 1][0] in labial and chunks[i + 1][0] != 'm':
                    chunks[i] = chunks[i][:-1] + 'p'

                elif chunks[i][-1] == 'n' and chunks[i + 1][0] in labial and chunks[i + 1][0] != 'm':
                    chunks[i] = chunks[i][:-1] + 'm'

                # before velars
                elif chunks[i][-1] in coronals and chunks[i + 1][0] in velars:
                    chunks[i] = chunks[i][:-1] + 'k'

                elif chunks[i][-1] == 'n' and chunks[i + 1][0] in velars:
                    chunks[i] = chunks[i][:-1] + 'ŋ'

                # before post_alveolar
                elif chunks[i][-1] in coronals and chunks[i + 1][0] in post_alveolar:
                    chunks[i] = chunks[i][:-1] + 'c'

                # labials and post alveolars assimilate to velars
                elif chunks[i][-1] in labial and chunks[i + 1][0] in velars and chunks[i][-1] != 'm':
                    chunks[i] = chunks[i][:-1] + 'k'

                elif chunks[i][-1] in labial and chunks[i + 1][0] in velars and chunks[i][-1] == 'm':
                    chunks[i] = chunks[i][:-1] + 'ŋ'

                elif chunks[i][-1] in post_alveolar and chunks[i + 1][0] in velars:
                    chunks[i] = chunks[i][:-1] + 'k'
            given = s.join(chunks)

        return given

    def patchims(self, given):
        # чтение патчимов
        seps = ['-', '#']
        vowels = ['ɐ', 'ʌ', 'o', 'ɨ', 'u', 'i', 'ɛ', 'e', 'ɰi']
        excepted = {'nʌlb': 'nʌp', 'pɐlb': 'pɐp'}
        first = {'ks': 'k', 'lg': 'k', 'nɟ': 'n', 'nh': 'n', 'lm': 'm', 'lb': 'l', 'ls': 'l', 'ltʰ': 'l', 'lh': 'l',
                 'lpʰ': 'p', 'ps': 'p'}
        second = {'t͈': 't', 'tʰ': 't', 's': 't', 's͈': 't', 'cʰ': 't', 'c': 't', 'c͈': 't', 'h': 't'}
        # конец слога перед согласной
        for s in seps:
            chunks = given.split(s)
            for i in range(len(chunks) - 1):
                if chunks[i + 1][0] not in vowels:
                    for root in excepted.keys():  # проверка на исключения
                        if root in chunks[i]:
                            chunks[i] = excepted[root]
                    for patchim in first.keys():
                        if patchim in chunks[i][-3:]:
                            chunks[i] = chunks[i].replace(patchim, first[patchim])
                    for patchim in second.keys():
                        if patchim in chunks[i][-2:]:
                            chunks[i] = chunks[i].replace(patchim, second[patchim])
            given = s.join(chunks)
        # абсолютный конец
        for root in excepted.keys():
            given = given.replace(root + '/', excepted[root] + '/')
        for patchim in first.keys():
            given = given.replace(patchim + '/', first[patchim] + '/')
        for patchim in second.keys():
            given = given.replace(patchim + '/', second[patchim] + '/')
        return given

    def voicing_and_h(self, given):  # должно быть после патчимов
        # фонетические переходы в позиции между гласными
        vowels = ['ɐ', 'ʌ', 'o', 'ɨ', 'u', 'i', 'ɛ', 'e', 'ɰi']
        to_voice = {'c': 'ɟ', 'k': 'g', 't': 'd', 'p': 'b', 'h': 'ɦ',
                    'cʲ': 'ɟʲ', 'kʲ': 'gʲ', 'tʲ': 'dʲ', 'pʲ': 'bʲ'}
        for tv in to_voice.keys():
            voiced = to_voice[tv]
            for v1 in vowels:
                for v2 in vowels:
                    given = given.replace(v1 + tv + '-' + v2, v1 + voiced + '-' + v2)
                    given = given.replace(v1 + '-' + tv + v2, v1 + '-' + voiced + v2)
            given = given.replace('n' + '-' + tv, 'n' + '-' + voiced)
            given = given.replace('m' + '-' + tv, 'm' + '-' + voiced)
            given = given.replace('l' + '-' + tv, 'l' + '-' + voiced)
            given = given.replace('ŋ' + '-' + tv, 'ŋ' + '-' + voiced)
            given = given.replace('n' + '#' + tv, 'n' + '#' + voiced)
            given = given.replace('m' + '#' + tv, 'm' + '#' + voiced)
            given = given.replace('l' + '#' + tv, 'l' + '#' + voiced)
            given = given.replace('ŋ' + '#' + tv, 'ŋ' + '#' + voiced)

        return given

    def pot(self, given):  # должно быть в самом конце
        obstr = ['k', 'p', 'c', 'cʰ', 'kʰ', 'tʰ',
                 'pʰ', 't', 'k͈', 't͈', 'p͈', 'c͈']
        for obs in obstr:
            given = given.replace(obs + '-k', obs + '-k͈')
            given = given.replace(obs + '-t', obs + '-t͈')
            given = given.replace(obs + '-p', obs + '-p͈')
            given = given.replace(obs + '-c', obs + '-c͈')

        return given

    def transcribe(self, given):
        given = self.borders.separator(given)
        given = self.exceptions(given)
        given = self.palatalization(given)
        given = self.yi(given)
        given = self.liquids(given)
        given = self.aspiration(given)
        given = self.stop_assim(given)
        given = self.spirantization(given)
        given = self.sonor_assim(given)
        given = self.coronal_asim(given)
        given = self.patchims(given)
        given = self.voicing_and_h(given)
        given = self.pot(given)
        return given
