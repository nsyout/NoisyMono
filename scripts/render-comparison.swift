import CoreGraphics
import CoreText
import Foundation
import ImageIO
import UniformTypeIdentifiers

struct Token {
    let text: String
    let color: CGColor
}

func rgb(_ hex: UInt32) -> CGColor {
    let red = CGFloat((hex >> 16) & 0xff) / 255
    let green = CGFloat((hex >> 8) & 0xff) / 255
    let blue = CGFloat(hex & 0xff) / 255
    return CGColor(red: red, green: green, blue: blue, alpha: 1)
}

func fail(_ message: String) -> Never {
    FileHandle.standardError.write(Data("error: \(message)\n".utf8))
    exit(1)
}

guard CommandLine.arguments.count == 4 else {
    fail("usage: render-comparison.swift FONT_FILE POSTSCRIPT_NAME OUTPUT_PNG")
}

let fontURL = URL(fileURLWithPath: CommandLine.arguments[1])
let expectedPostScriptName = CommandLine.arguments[2]
let outputURL = URL(fileURLWithPath: CommandLine.arguments[3])

var registrationError: Unmanaged<CFError>?
if !CTFontManagerRegisterFontsForURL(fontURL as CFURL, .process, &registrationError) {
    let description = registrationError?.takeRetainedValue().localizedDescription ?? "unknown error"
    fail("could not register \(fontURL.lastPathComponent): \(description)")
}

let width = 1364
let height = 984
let fontSize: CGFloat = 42
let font = CTFontCreateWithName(expectedPostScriptName as CFString, fontSize, nil)
let actualPostScriptName = CTFontCopyPostScriptName(font) as String
guard actualPostScriptName == expectedPostScriptName else {
    fail("requested \(expectedPostScriptName), Core Text selected \(actualPostScriptName)")
}

guard let context = CGContext(
    data: nil,
    width: width,
    height: height,
    bitsPerComponent: 8,
    bytesPerRow: 0,
    space: CGColorSpaceCreateDeviceRGB(),
    bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
) else {
    fail("could not create bitmap context")
}

// Flexoki Dark: https://stephango.com/flexoki
let background = rgb(0x100F0F)
let panel = rgb(0x1C1B1A)
let border = rgb(0x343331)
let text = rgb(0xCECDC3)
let muted = rgb(0x878580)
let faint = rgb(0x575653)
let red = rgb(0xD14D41)
let orange = rgb(0xDA702C)
let yellow = rgb(0xD0A215)
let green = rgb(0x879A39)
let cyan = rgb(0x3AA99F)
let blue = rgb(0x4385BE)
let purple = rgb(0x8B7EC8)
let magenta = rgb(0xCE5D97)

context.setFillColor(background)
context.fill(CGRect(x: 0, y: 0, width: width, height: height))

let panelRect = CGRect(x: 44, y: 44, width: width - 88, height: height - 88)
context.setFillColor(panel)
context.fill(panelRect)
context.setStrokeColor(border)
context.setLineWidth(2)
context.stroke(panelRect)

let swatchWidth = panelRect.width / 8
for (index, color) in [red, orange, yellow, green, cyan, blue, purple, magenta].enumerated() {
    context.setFillColor(color)
    context.fill(CGRect(
        x: panelRect.minX + CGFloat(index) * swatchWidth,
        y: panelRect.maxY - 8,
        width: swatchWidth,
        height: 8
    ))
}

let lines: [[Token]] = [
    [Token(text: "// Same source. Regular weight. Font defaults.", color: faint)],
    [],
    [
        Token(text: "const ", color: magenta),
        Token(text: "glyphs ", color: text),
        Token(text: "= ", color: cyan),
        Token(text: "\"0O 1Il gq | {}[]()\"", color: green),
        Token(text: ";", color: muted),
    ],
    [
        Token(text: "if ", color: magenta),
        Token(text: "(score ", color: text),
        Token(text: "!= ", color: cyan),
        Token(text: "0", color: orange),
        Token(text: ") {", color: muted),
    ],
    [
        Token(text: "    const ", color: magenta),
        Token(text: "ratio ", color: text),
        Token(text: "= ", color: cyan),
        Token(text: "10.25", color: orange),
        Token(text: ";", color: muted),
    ],
    [
        Token(text: "    console", color: text),
        Token(text: ".", color: muted),
        Token(text: "log", color: blue),
        Token(text: "(", color: muted),
        Token(text: "`value -> ${ratio}`", color: green),
        Token(text: ");", color: muted),
    ],
    [
        Token(text: "    return ", color: magenta),
        Token(text: "{ ok", color: text),
        Token(text: ": ", color: muted),
        Token(text: "true", color: purple),
        Token(text: " };", color: muted),
    ],
    [Token(text: "}", color: muted)],
    [Token(text: "// Prose — one cell, clean rhythm.", color: faint)],
    [
        Token(text: "const ", color: magenta),
        Token(text: "compare ", color: text),
        Token(text: "= ", color: cyan),
        Token(text: "(a, b) ", color: text),
        Token(text: "=> ", color: cyan),
        Token(text: "a ", color: text),
        Token(text: "<= ", color: cyan),
        Token(text: "b ", color: text),
        Token(text: "&& ", color: cyan),
        Token(text: "b ", color: text),
        Token(text: ">= ", color: cyan),
        Token(text: "a", color: text),
        Token(text: ";", color: muted),
    ],
]

let fontKey = NSAttributedString.Key(kCTFontAttributeName as String)
let colorKey = NSAttributedString.Key(kCTForegroundColorAttributeName as String)
let x: CGFloat = 104
let firstBaseline: CGFloat = CGFloat(height) - 154
let lineHeight: CGFloat = 72

context.textMatrix = .identity

for (lineIndex, tokens) in lines.enumerated() {
    let attributed = NSMutableAttributedString()
    for token in tokens {
        attributed.append(NSAttributedString(
            string: token.text,
            attributes: [
                fontKey: font,
                colorKey: token.color,
            ]
        ))
    }

    guard attributed.length > 0 else {
        continue
    }

    let line = CTLineCreateWithAttributedString(attributed)
    context.textPosition = CGPoint(
        x: x,
        y: firstBaseline - CGFloat(lineIndex) * lineHeight
    )
    CTLineDraw(line, context)
}

guard let image = context.makeImage() else {
    fail("could not create image")
}

guard let destination = CGImageDestinationCreateWithURL(
    outputURL as CFURL,
    UTType.png.identifier as CFString,
    1,
    nil
) else {
    fail("could not create PNG destination")
}

CGImageDestinationAddImage(destination, image, [
    kCGImagePropertyPNGDictionary: [
        kCGImagePropertyPNGInterlaceType: 0,
    ],
] as CFDictionary)

guard CGImageDestinationFinalize(destination) else {
    fail("could not write \(outputURL.path)")
}
