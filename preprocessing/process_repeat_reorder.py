# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
import os, json



class Processor():
    # re-order
    def reorder(self, re_order, slices):
        file_type = '.' + slices[0].split('.')[1]
        tmp = []
        if re_order == 'reverse':
            tmp = slices[::-1]
        elif '+' in re_order:
            spans = re_order.split('+')
            for span in spans:
                if '-' in span:# a span of images
                    left, right = [int(x) for x in span.split('-')]
                    for idx in range(left, right+1):
                        file_name = self.idx_to_name(idx) + file_type
                        if file_name in slices:
                            # print(f"{file_name} not exits")
                            tmp.append(file_name)
                else: # single image
                    idx = int(span)
                    file_name = self.idx_to_name(idx) + file_type
                    if file_name in slices:
                        # print(f"{file_name} not exits")
                        tmp.append(file_name)
        elif '-' in re_order:
            left, right = [int(x) for x in re_order.split('-')]
            for idx in range(left, right+1):
                file_name = self.idx_to_name(idx) + file_type
                if file_name in slices:
                    # print(f"{file_name} not exits")
                    tmp.append(file_name)
        return tmp

    # remove noisy data
    def rm_span(self, left, right, slices):
        file_type = '.' + slices[0].split('.')[1]
        for idx in range(left, right+1):
            file_name = self.idx_to_name(idx) + file_type
            if file_name in slices: slices.remove(file_name)
        return slices

    def rm_single(self, idx, slices):
        file_type = '.' + slices[0].split('.')[1]
        idx = int(idx)
        file_name = self.idx_to_name(idx) + file_type
        if file_name in slices: slices.remove(file_name)
        return slices

    def remove_noise(self, repeat_ids, slices):
        file_type = '.' + slices[0].split('.')[1]
        tmp = []
        if repeat_ids == 'discard':
            return tmp
        elif ';' in repeat_ids:
            spans = repeat_ids.split(';')
            tmp = slices
            for span in spans:
                if '-' in span:
                    left, right = [int(x) for x in span.split('-')]
                    tmp = self.rm_span(left, right, tmp)
                else:
                    tmp = self.rm_single(span, tmp)
        elif '-' in repeat_ids:
            left, right = [int(x) for x in repeat_ids.split('-')]
            tmp = self.rm_span(left, right, slices)
        else:
            tmp = self.rm_single(repeat_ids, slices)
        return tmp

    def process(self, debug=False, CT=CT):
        # if debug: set_trace()
        try:
            for line in data:
                cls_name, pid, scan_id, is_seg, is_repeat, repeat_ids, re_order = line.split(',')
                slice_path = f"./{cls_name}/{pid}/{scan_id}"
                slices = os.listdir(slice_path)
                if len(slices) == 0:
                    print(f'there is no image in {line}')
                    continue
                if pid not in CT[cls_name]: CT[cls_name][pid] = {}
                if re_order:
                    slices = self.reorder(re_order, slices)
                if is_repeat=='1' or repeat_ids:
                    slices = self.remove_noise(repeat_ids, slices)
                if len(slices)>0: CT[cls_name][pid][scan_id] = slices
            with open('CT_data.json', 'w') as f:
                json.dump(CT,f, indent=4, sort_keys=True)
                print("Saving CT data to CT_data.json")
        except Exception as e:
            print(e)

    @staticmethod
    def idx_to_name(idx):
        return f"{idx:04d}"


if __name__ == '__main__':
    with open('CT_cleaned_v2.csv', 'r') as f:
        data = f.read().split('\n')
        print(data[0])
        data = data[1:]
        print(data[1240:1250])

    CT = {'CP':{}, 'NCP':{}, 'Normal':{}}
    processor = Processor()
    debug = False
    # debug = True
    processor.process(debug, CT)