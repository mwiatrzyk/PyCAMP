import os

from camp.plugins.ocr import OCRPluginBase


class Tesseract(OCRPluginBase):
    __ocr_command__ = 'tesseract %(infile)s %(outfile)s'

    def create_infile(self, segment, angle=None):
        infile = os.path.join(self.working_dir, '%d_%d_%d_%d.tif' % segment.bounds)
        segment.toimage(color=0, background=255, border=2, angle=angle).save(infile)
        return infile
    
    def get_result(self, segment, infile):
        outfile = os.path.join(self.working_dir, '%d_%d_%d_%d' % segment.bounds)
        if self.execute(infile=infile, outfile=outfile):
            return open("%s.txt" % outfile).read().strip()
    
    def recognized(self, result):
        return result and '\n' not in result
