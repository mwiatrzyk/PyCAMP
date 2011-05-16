import os

from camp.plugins.ocr import OCRPluginBase


class Gocr(OCRPluginBase):
    __ocr_command__ = 'djpeg -pnm -gray %(infile)s | gocr -o %(outfile)s -'
    __ocr_priority__ = 1

    def create_infile(self, segment, angle=None):
        infile = os.path.join(self.working_dir, '%d_%d_%d_%d.jpg' % segment.bounds)
        segment.toimage(color=0, background=255, border=2, angle=angle).save(infile)
        return infile
    
    def get_result(self, segment, infile):
        outfile = os.path.join(self.working_dir, '%d_%d_%d_%d.txt' % segment.bounds)
        if self.execute(infile=infile, outfile=outfile):
            return open(outfile).read().strip()
    
    def recognized(self, result):
        return result and '\n' not in result
